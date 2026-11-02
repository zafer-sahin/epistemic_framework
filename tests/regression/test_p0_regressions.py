import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import z3

from core.exceptions import DiachronicViolationError
from core.models import OntologyLoader
from core.logic_engine import AristotelianSolver
from core.layer1_graph import Layer1HeuristicGraph
from core.layer2_rules import Layer2RuleEngine
from core.layer3_smt import Layer3SMTCircuitBreaker
from core.epistemic_orchestrator import EpistemicOrchestrator, CONSISTENT_STATUSES
from core.syllogism_builder import SyllogismEngine
from linguistics.tokenizer import EpistemicTokenizer
from linguistics.sarf_parser import SarfEngine, LocalOntoLexGraphClient
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.contextual_lexicon import ContextualLexicon, LocalOntoLexSemanticClient
from linguistics.discourse_state import DiscourseRegister
from linguistics.ilm_wad_adapter import IlmWadAdapter, SemanticStatementIR
from schools.ashari_usul import AshariUsul
from schools.salafi_usul import SalafiUsul
from schools.taftazani.adab_al_bahth import AdabAlBahthEngine

"""
.. felsefe_notu:: P0 Regresyon Matrisi
    İş ve implementasyon incelemesinde P0 olarak sınıflanan hataların her biri burada
    çalıştırılabilir bir teste dönüştürülmüştür. Henüz düzeltilmemiş bulgular
    `unittest.expectedFailure` ile işaretlidir; ilgili hata düzeltildiğinde test
    "beklenmeyen başarı" (unexpected success) verir ve dekoratör kaldırılmalıdır.
"""

ONTOLOGY_PATH = Path("data/base_ontology.json")


def _boru_hatti_kur(max_cache_size: int = 1000) -> SimpleNamespace:
    """run_simulation.py ile aynı leksikon kayıtlarına sahip taze bir N-Tier boru hattı kurar."""
    ontology = OntologyLoader().load(ONTOLOGY_PATH)
    solver = AristotelianSolver(ontology)
    lexicon = ContextualLexicon(semantic_client=LocalOntoLexSemanticClient())
    discourse = DiscourseRegister()

    lexicon.register_word("yad", "Salafi", "Sifat_Yed_Literal")
    lexicon.register_word("yad", "Salafi", "Sifat_Yed_Bila_Kayf", proposition_type="Kadiyye-i_Hamliyye", sibak_trigger="allah")
    for namespace in ("Ashari", "Maturidi"):
        lexicon.register_word("yad", namespace, "Sifat_Yed_Literal", proposition_type="Kadiyye-i_Hamliyye")
        lexicon.register_word("yad", namespace, "Sifat_Yed_Metaphor", proposition_type="Metaphor_Fallback")
    lexicon.register_word("feres", "Base", "Feres")

    adapter = IlmWadAdapter(lexicon, discourse)
    l1 = Layer1HeuristicGraph(ontology)
    l2 = Layer2RuleEngine()
    l3 = Layer3SMTCircuitBreaker(solver, timeout_ms=3000, max_cache_size=max_cache_size)
    return SimpleNamespace(
        ontology=ontology, solver=solver, lexicon=lexicon, discourse=discourse, adapter=adapter,
        l1=l1, l2=l2, l3=l3, orchestrator=EpistemicOrchestrator(adapter, l1, l2, l3),
        tokenizer=EpistemicTokenizer(), sarf=SarfEngine(graph_client=LocalOntoLexGraphClient()),
        nahiv=NahivDependencyCompiler(),
    )


def _cozumle(p: SimpleNamespace, cumle: str):
    tokens = p.tokenizer.tokenize(cumle)
    morph = p.sarf.derive_lexicon(tokens)
    return tokens, morph, p.nahiv.suggest_dependencies(tokens, morph)


def _hukum(p: SimpleNamespace, cumle: str, usul) -> dict:
    tokens, morph, deps = _cozumle(p, cumle)
    p.discourse.clear_memory()
    return p.orchestrator.process_statement(tokens, deps, usul, morph)


def _ir(p: SimpleNamespace, cumle: str, namespace: str = "Ashari") -> SemanticStatementIR:
    tokens, morph, deps = _cozumle(p, cumle)
    p.discourse.clear_memory()
    return p.adapter.generate_ir(tokens, deps, namespace, morph)


def _z3_ifadeleri(p: SimpleNamespace, ir: SemanticStatementIR) -> list:
    """IR'yi L3'ün kullandığı temel dünya/zaman/mekân sabitleriyle Z3 ifadelerine derler."""
    b = p.solver.builder
    sabitler = (z3.Const("w_base", b.WorldSort), z3.Const("tz_base", b.TimeSortZati),
                z3.Const("tv_base", b.TimeSortVasfi), z3.Const("s_base", b.SpaceSort))
    return [p.l3._build_z3_expr(item, *sabitler) for item in ir.predicates]


def _olumsuzluk_icerir(ifade: z3.ExprRef) -> bool:
    if z3.is_not(ifade):
        return True
    if z3.is_quantifier(ifade):
        return _olumsuzluk_icerir(ifade.body())
    return any(_olumsuzluk_icerir(c) for c in ifade.children())


def _celiskili_mucib_iddiasi() -> SemanticStatementIR:
    """Ontolojiyle tek başına çelişen iddia: aynı varlık hem Cemad hem İnsan (run_simulation Senaryo 5)."""
    return SemanticStatementIR(
        active_namespace="Ashari", active_agent="Mujib", is_valid_for_z3=True,
        predicates=[("Cemad", "Cemad", 1), ("Insan", "Insan", 1), ("Rel_Mubteda_Haber", "Cemad::Insan", 2)],
    )


def _munazara_delile_kadar(solver: AristotelianSolver, discourse: DiscourseRegister) -> AdabAlBahthEngine:
    """Döngüsel olmayan bir delille AWAITING_ATTACK durumuna gelmiş münazara."""
    fsm = AdabAlBahthEngine(solver, discourse)
    fsm.submit_claim("Exists([x], Cism(x))")
    fsm.tahrir_i_niza(["Cevher"], ["Cism"])
    fsm.submit_evidence(["Exists([x], Cemad(x))"])
    return fsm


def _repl_kur():
    """REPL'i açılış mesajlarını bastırarak kurar."""
    from repl import EpistemicShell
    with redirect_stdout(io.StringIO()):
        return EpistemicShell()


class TestP0_1_ReplBaslatma(unittest.TestCase):
    """[P0-1] README'nin son kullanıcı arayüzü olan REPL açılabilmelidir."""

    def test_repl_starts_without_exit(self):
        try:
            _repl_kur()
        except SystemExit as exc:
            self.fail(f"REPL başlatılırken sys.exit({exc.code}) çağrıldı.")

    def test_repl_lexicon_still_rejects_modern_epoch(self):
        """Açılıştan kaldırılan 'Modern' kaydının yerini alır: koruma REPL'in kendi sözlüğünde çalışmalı."""
        shell = _repl_kur()
        with self.assertRaises(DiachronicViolationError):
            shell.lexicon.register_word("demokrasi", "Base", "Sekuler_Otorite", epoch="Modern")
        self.assertNotIn("demokrasi", shell.lexicon.dump_tensor(), "Reddedilen kayıt sözlüğe yazılmamalı.")


class TestP0_2_TevilKopruleri(unittest.TestCase):
    """[P0-2] Bir cümlenin te'vil köprüsü, sonraki cümlelerin ve diğer ekollerin hükmüne sızmamalıdır."""

    def test_tevil_itself_still_succeeds_and_names_its_bridges(self):
        sonuc = _hukum(_boru_hatti_kur(), "yadu allahi", AshariUsul())
        self.assertEqual(sonuc["status"], "SAT")
        self.assertTrue(sonuc.get("tevil_applied"))
        self.assertTrue(sonuc.get("tevil_bridges"), "Te'vilin dayandığı köprüler sonuçta adlarıyla görünmeli.")

    def test_bridge_does_not_change_later_sentence_in_same_school(self):
        taze = _hukum(_boru_hatti_kur(), "zeydun daribun", AshariUsul())["status"]
        p = _boru_hatti_kur()
        _hukum(p, "yadu allahi", AshariUsul())
        sonra = _hukum(p, "zeydun daribun", AshariUsul())["status"]
        self.assertEqual(sonra, taze, "Önceki cümlenin te'vil köprüsü 'zeydun daribun' hükmünü değiştirdi.")

    def test_bridge_does_not_leak_into_other_school(self):
        taze = _hukum(_boru_hatti_kur(), "zeydun daribun", SalafiUsul())["status"]
        p = _boru_hatti_kur()
        _hukum(p, "yadu allahi", AshariUsul())
        sonra = _hukum(p, "zeydun daribun", SalafiUsul())["status"]
        self.assertEqual(sonra, taze, "Eş'arî te'vil köprüsü Selefî profilin hükmüne sızdı.")

    def test_bridge_axioms_are_scoped_and_named_in_unsat_core(self):
        p = _boru_hatti_kur()
        kopruler = p.l3.prove_metaphorical_bridge(p.l1.find_mana_el_mana_chain("Bats", "Kudret"))
        ir = SemanticStatementIR(active_namespace="Ashari", active_agent="Mujib", is_valid_for_z3=True,
                                 predicates=[("Bats", "Bats", 1)])

        sonuc = p.l3.execute_sat_check(ir, bridge_axioms=kopruler)
        self.assertEqual(sonuc["status"], "UNSAT")
        self.assertIn("AXIOM_BEYAN_", sonuc["message"], "Çelişkiye katılan köprü, unsat core'da adıyla görünmeli.")
        self.assertEqual(p.l3.execute_sat_check(ir)["status"], "SAT", "Köprü yalnızca verildiği kontrolde geçerli olmalı.")


class TestP0_3_Onbellek(unittest.TestCase):
    """[P0-3] Önbellek mantıksal sonucu değiştirmemeli: anahtar bağlamı içermeli, boyut hükmü etkilememeli."""

    def test_results_do_not_depend_on_cache_size(self):
        akis = [("zeydun daribun", AshariUsul), ("yadu allahi", AshariUsul), ("zeydun daribun", AshariUsul)]

        def calistir(boyut: int) -> list:
            p = _boru_hatti_kur(max_cache_size=boyut)
            return [_hukum(p, cumle, usul())["status"] for cumle, usul in akis]

        self.assertEqual(calistir(1), calistir(1000))

    def test_cache_respects_solver_context(self):
        p = _boru_hatti_kur()
        ir = _ir(p, "zeydun daribun")
        self.assertEqual(p.l3.execute_sat_check(ir)["status"], "SAT")

        b = p.solver.builder
        bats = b.get_or_create_predicate("Bats")
        x = z3.Const("x_p0_3", b.EntitySort)
        sabitler = (z3.Const("w_base", b.WorldSort), z3.Const("tz_base", b.TimeSortZati),
                    z3.Const("tv_base", b.TimeSortVasfi), z3.Const("s_base", b.SpaceSort))
        p.solver.solver.push()
        try:
            p.solver.solver.add(z3.ForAll([x], z3.Not(bats(*sabitler, x))))
            self.assertEqual(p.l3.execute_sat_check(ir)["status"], "UNSAT",
                             "Çözücü bağlamı değiştiği halde önbellekteki eski sonuç döndü.")
        finally:
            p.solver.solver.pop()
        self.assertEqual(p.l3.execute_sat_check(ir)["status"], "SAT")


class TestP0_4_MunazaraScopeDengesi(unittest.TestCase):
    """[P0-4] Münazara, paylaşılan çözücüde açtığı kapsamı kapatmalı ve yabancı kapsamlara dokunmamalıdır."""

    def test_cross_school_muaradah_does_not_leak_scope_into_next_session(self):
        p = _boru_hatti_kur()
        fsm = _munazara_delile_kadar(p.solver, p.discourse)
        self.assertEqual(fsm.current_state, "AWAITING_ATTACK")

        tokens, morph, deps = _cozumle(p, "nami zeydun")
        p.orchestrator.execute_cross_school_muaradah(
            _celiskili_mucib_iddiasi(), AshariUsul(), tokens, deps, SalafiUsul(), morph, fsm_engine=fsm)
        fsm.reset_session()

        self.assertEqual(p.solver.solver.num_scopes(), 0, "Münazaranın delil kapsamı çözücüde açık kaldı.")
        yeni = AdabAlBahthEngine(p.solver, p.discourse)
        self.assertEqual(yeni.submit_claim("Exists([x], Cemad(x))")["status"], "AWAITING_TAHRIR",
                         "Önceki münazaranın öncülü yeni oturumda aksiyom gibi davrandı.")

    def test_reset_session_does_not_pop_foreign_scope(self):
        p = _boru_hatti_kur()
        fsm = AdabAlBahthEngine(p.solver, p.discourse)
        fsm.submit_claim("Exists([x], Cism(x))")
        fsm.tahrir_i_niza(["Cevher"], ["Cism"])
        self.assertEqual(fsm.current_state, "AWAITING_EVIDENCE")

        p.solver.solver.push()
        try:
            fsm.reset_session()
            self.assertEqual(p.solver.solver.num_scopes(), 1, "reset_session başka bir bileşenin kapsamını kapattı.")
        finally:
            while p.solver.solver.num_scopes():
                p.solver.solver.pop()

    def test_attack_after_recursive_men_keeps_scopes_balanced(self):
        """[P1-5] Aynı kök neden: men' savunulduktan sonra ana iddiaya saldırı çökmemeli."""
        p = _boru_hatti_kur()
        fsm = AdabAlBahthEngine(p.solver, p.discourse)
        fsm.submit_claim("Exists([x], Nami(x))")
        fsm.tahrir_i_niza(["Cism"], ["Nami"])
        fsm.submit_evidence(["Exists([x], Hayvan(x))", "Forall([x], Implies(Hayvan(x), Nami(x)))"])
        fsm.attack_evidence("Men", "Exists([x], Hayvan(x))")
        fsm.tahrir_i_niza(["Cism"], ["Hayvan"])
        fsm.submit_evidence(["Exists([x], Insan(x))"])
        self.assertEqual(fsm.attack_evidence("Nakz")["status"], "SUB_CLAIM_PROVEN")

        sonuc = fsm.attack_evidence("Nakz")
        self.assertNotEqual(sonuc["status"], "NAKZ_SUCCESS", "Geçerli ana delil nakzedilmiş sayıldı.")
        fsm.reset_session()
        self.assertEqual(p.solver.solver.num_scopes(), 0)

    def test_repl_gives_fsm_its_own_solver(self):
        shell = _repl_kur()
        self.assertIsNot(shell.fsm.solver, shell.l3.core_solver,
                         "FSM ile L3 aynı çözücüyü paylaşıyor; münazara kapsamları cümle hükümlerine karışır.")


class TestP0_5_Haml(unittest.TestCase):
    """[P0-5] Haml mantıksal içerik taşımalı; izafet özdeşlik sayılmamalıdır."""

    def test_predication_contradiction_is_detected(self):
        p = _boru_hatti_kur()
        sonuc = p.l3.execute_sat_check(_ir(p, "zeydun feresun"))
        self.assertEqual(sonuc["status"], "UNSAT", "'Zeyd attır' ontolojideki İnsan/Feres ayrıklığıyla çelişmeli.")

    def test_accident_is_predicated_by_subsistence(self):
        """Haml-i iştikâk: 'Zeyd dâribdir'. Darb (araz) Zeyd'in kendisi değil, Zeyd'de kâim olandır."""
        p = _boru_hatti_kur()
        sonuc = p.l3.execute_sat_check(_ir(p, "zeydun daribun"))
        self.assertEqual(sonuc["status"], "SAT", sonuc["message"])

    def test_individual_is_not_the_species_constant(self):
        """Zeyd İnsan'ın bir ferdidir; ferdin sabiti nev'in adı olursa aynı nev'in bütün fertleri tek sabite çöker."""
        p = _boru_hatti_kur()
        insan_fertleri = [item[1] for item in _ir(p, "zeydun feresun").predicates
                          if isinstance(item, tuple) and item[0] == "Insan" and item[2] == 1]
        self.assertTrue(insan_fertleri)
        self.assertNotIn("Insan", insan_fertleri, "Zeyd, nev'i olan İnsan'ın sabitine çöktü.")

    def test_spatial_relation_keeps_the_natures_of_its_terms(self):
        """Mekân bağı fertleri bağlar; fertlerin mâhiyetleri IR'de yazılı kalmalı. Vâcib mekânda bulunmaz (tenzih)."""
        p = _boru_hatti_kur()
        sonuc = p.l3.execute_sat_check(_ir(p, "allahu fi semai"))
        self.assertEqual(sonuc["status"], "UNSAT", sonuc["message"])
        self.assertIn("AXIOM_TENZIH_WAJIB_AL_WUJUD", sonuc["message"])

    def test_pronoun_refers_to_the_individual_of_its_antecedent(self):
        """Zamir, merciinin nev'ine değil ferdine döner."""
        discourse = DiscourseRegister()
        discourse.add_mention("zeydun", "Insan", "Ashari", gender="Muzekker", number="Mufred", referent="zeyd")
        merci = discourse.resolve_antecedent("huve")
        self.assertEqual((merci.ontologic_id, merci.referent), ("Insan", "zeyd"))

    def test_izafet_is_not_identity(self):
        p = _boru_hatti_kur()
        ifadeler = _z3_ifadeleri(p, _ir(p, "yadu allahi", "Salafi"))
        self.assertFalse(any(z3.is_eq(e) for e in ifadeler), "İzafet (sıfat–zât) özdeşliğe çevrildi.")

    def test_izafet_of_substance_to_wajib_is_consistent(self):
        """İzafet-i teşrîf: 'Beytullah'. Ev Allah'a nisbet edilir; Allah'la özdeş sayılmaz, O'nda kâim de olmaz."""
        p = _boru_hatti_kur()
        sonuc = p.l3.execute_sat_check(_ir(p, "beytu allahi"))
        self.assertEqual(sonuc["status"], "SAT", sonuc["message"])

    def test_literal_hand_contradicts_tenzih_through_subsistence(self):
        """Eş'arî lafzî okumada 'yed' bir arazdır ve izafetle Allah'ta kâim olur; Vâcib havâdisin mahalli olamaz."""
        p = _boru_hatti_kur()
        sonuc = p.l3.execute_sat_check(_ir(p, "yadu allahi", "Ashari"))
        self.assertEqual(sonuc["status"], "UNSAT")
        self.assertIn("AXIOM_TENZIH_MAHALL_I_HAVADIS", sonuc["message"])


class TestP0_6_Olumsuzluk(unittest.TestCase):
    """[P0-6] Olumsuz önerme temsil edilebilmeli; 'lâ' tevkîd sayılmamalıdır."""

    def test_la_is_not_classified_as_emphasis(self):
        sinif = LocalOntoLexGraphClient().query_closed_set("la") or {}
        self.assertNotEqual(sinif.get("ontologic_type"), "Harf_Tevkid")

    def test_attached_lam_remains_emphasis(self):
        """Kelimeye bitişik 'la-' lâm-ı tevkîddir; tek başına yazılan nefy edatı 'lâ' ile karışmamalı."""
        lam = EpistemicTokenizer().tokenize("lazeydun")[0]
        self.assertEqual(LocalOntoLexGraphClient().query_closed_set(lam)["ontologic_type"], "Harf_Tevkid")

    def test_laysa_is_a_negation_particle(self):
        """'laysa' isim cümlesinin nefy fiilidir; 'la' + 'ysa' diye bölünmemeli."""
        ilk = EpistemicTokenizer().tokenize("laysa zeydun cemaden")[0]
        self.assertEqual(ilk, "laysa")
        self.assertEqual(LocalOntoLexGraphClient().query_closed_set(ilk)["ontologic_type"], "Harf_Nefy")

    def test_negative_sentence_is_represented_with_negation(self):
        p = _boru_hatti_kur()
        ir = _ir(p, "zeydun la yadribu")
        self.assertTrue(ir.is_valid_for_z3, "Olumsuz haber cümlesi pragmatik ihlal sayıldı.")
        self.assertTrue(any(_olumsuzluk_icerir(e) for e in _z3_ifadeleri(p, ir)), "IR'de olumsuzluk yok.")

    def test_negative_sentence_is_consistent(self):
        p = _boru_hatti_kur()
        ir = _ir(p, "zeydun la yadribu")
        self.assertTrue(ir.is_valid_for_z3 and ir.predicates, "Olumsuz haber cümlesi IR'ye dönüşmedi.")
        sonuc = p.l3.execute_sat_check(ir)
        self.assertEqual(sonuc["status"], "SAT", sonuc["message"])

    def test_negation_contradicts_its_affirmation(self):
        """Tenâkuz: 'Zeyd vurur' ile 'Zeyd vurmaz' birlikte doğru olamaz."""
        p = _boru_hatti_kur()
        sonuc = p.l3.execute_joint_sat_check({"Mujib": _ir(p, "zeydun yadribu"), "Sail": _ir(p, "zeydun la yadribu")})
        self.assertEqual(sonuc["status"], "UNSAT", sonuc["message"])

    def test_muaradah_with_the_contradictory_reading_succeeds(self):
        """Mucîb 'Zeyd vurur' der, Sâil 'Zeyd vurmaz' okumasıyla karşı çıkar: çatışma ontolojiye değil tenâkuza dayanır."""
        p = _boru_hatti_kur()
        tokens, morph, deps = _cozumle(p, "zeydun yadribu")
        p.discourse.clear_memory()
        mucib_sonucu, mucib_okumasi = p.orchestrator.evaluate_statement(tokens, deps, AshariUsul(), morph)
        self.assertIn(mucib_sonucu["status"], CONSISTENT_STATUSES, mucib_sonucu.get("message"))

        tokens, morph, deps = _cozumle(p, "zeydun la yadribu")
        p.discourse.set_agent("Sail")
        sonuc = p.orchestrator.execute_cross_school_muaradah(mucib_okumasi, AshariUsul(), tokens, deps, SalafiUsul(), morph)
        self.assertEqual(sonuc["status"], "MUARADAH_SUCCESS", sonuc["message"])
        self.assertEqual(sonuc["conflict"]["axioms"], [])
        self.assertIn("tenâkuz", sonuc["message"])

    def test_negating_what_the_subject_is_contradicts_its_nature(self):
        """Sâlibe, mübtedanın ferdini haberin altına giren her şeyden ayırır: 'Zeyd cisim değildir' İnsan'la çelişir."""
        p = _boru_hatti_kur()
        p.lexicon.register_word("cism", "Base", "Cism")
        sonuc = p.l3.execute_sat_check(_ir(p, "laysa zeydun cismen"))
        self.assertEqual(sonuc["status"], "UNSAT", sonuc["message"])

    def test_negated_tenzih_is_accepted_by_every_school(self):
        """'Allah cisim değildir' tenzihtir; olumsuzlanan bir nisbet mecaz adayı (karîne-i mânia) değildir."""
        p = _boru_hatti_kur()
        p.lexicon.register_word("cism", "Base", "Cism")
        for usul in (AshariUsul(), SalafiUsul()):
            with self.subTest(usul=usul.namespace):
                sonuc = _hukum(p, "laysa allahu cismen", usul)
                self.assertEqual(sonuc["status"], "SAT", sonuc.get("message") or sonuc.get("reason"))


class TestP0_7_Muaraza(unittest.TestCase):
    """[P0-7] Mu'âraza aynı ontolojiyle değerlendirilmeli; içerikten bağımsız sonuç üretmemelidir."""

    def _okuma(self, p: SimpleNamespace, cumle: str, usul) -> SemanticStatementIR:
        """Cümlenin, usûlün tutarlı bulduğu (te'vil uygulandıysa te'vil sonrası) okuması."""
        tokens, morph, deps = _cozumle(p, cumle)
        p.discourse.clear_memory()
        sonuc, okuma = p.orchestrator.evaluate_statement(tokens, deps, usul, morph)
        self.assertIn(sonuc["status"], CONSISTENT_STATUSES, sonuc.get("message"))
        return okuma

    def _capraz_muaraza(self, p: SimpleNamespace, mucib_okumasi, mucib_usul, cumle: str, sail_usul) -> dict:
        tokens, morph, deps = _cozumle(p, cumle)
        p.discourse.set_agent("Sail")
        return p.orchestrator.execute_cross_school_muaradah(mucib_okumasi, mucib_usul, tokens, deps, sail_usul, morph)

    def test_counter_claim_refuted_by_premise_is_not_stalemate(self):
        ontology = OntologyLoader().load(ONTOLOGY_PATH)
        fsm = _munazara_delile_kadar(AristotelianSolver(ontology), DiscourseRegister())
        sonuc = fsm.attack_evidence("Muaradah", "Forall([x], Not(Cism(x)))")
        self.assertEqual(sonuc["status"], "MUARADAH_FAILED",
                         "Kabul edilmiş öncülle (∃Cemad ⊆ Cism) çelişen karşı-iddia kilitlenme sayıldı.")

    def test_counter_claim_not_against_the_claim_is_not_stalemate(self):
        """Delille bağdaşan ama iddianın hilâfını gerektirmeyen karşı-iddia, iddiaya yöneltilmiş bir mu'âraza değildir."""
        ontology = OntologyLoader().load(ONTOLOGY_PATH)
        fsm = _munazara_delile_kadar(AristotelianSolver(ontology), DiscourseRegister())
        sonuc = fsm.attack_evidence("Muaradah", "Exists([x], Insan(x))")
        self.assertEqual(sonuc["status"], "MUARADAH_FAILED", sonuc["message"])

    def test_counter_claim_not_excluded_by_evidence_is_stalemate(self):
        """Delil iddiayı karşı-iddiaya karşı ispatlamıyorsa (∃Cevher, ∃Cism'i gerektirmez) kilitlenme çıkabilmeli."""
        fsm = AdabAlBahthEngine(AristotelianSolver(OntologyLoader().load(ONTOLOGY_PATH)), DiscourseRegister())
        fsm.submit_claim("Exists([x], Cism(x))")
        fsm.tahrir_i_niza(["Cevher"], ["Cism"])
        fsm.submit_evidence(["Exists([x], Cevher(x))"])
        sonuc = fsm.attack_evidence("Muaradah", "Forall([x], Not(Cism(x)))")
        self.assertEqual(sonuc["status"], "STALEMATE", sonuc["message"])

    def test_undecided_solver_is_not_a_verdict_in_fsm(self):
        """Çözücü karar veremezse (UNKNOWN) mu'âraza bir hükümle bitmemeli; münazara açık kalmalı."""
        solver = AristotelianSolver(OntologyLoader().load(ONTOLOGY_PATH))
        fsm = _munazara_delile_kadar(solver, DiscourseRegister())
        with mock.patch.object(solver.solver, "check", return_value=z3.unknown):
            sonuc = fsm.attack_evidence("Muaradah", "Forall([x], Not(Cism(x)))")
        self.assertEqual(sonuc["status"], "MUARADAH_UNDECIDED", sonuc["message"])
        self.assertEqual(fsm.current_state, "AWAITING_ATTACK")

    def test_self_contradictory_mujib_claim_does_not_win(self):
        p = _boru_hatti_kur()
        iddia = _celiskili_mucib_iddiasi()
        self.assertEqual(p.l3.execute_sat_check(iddia)["status"], "UNSAT")

        tokens, morph, deps = _cozumle(p, "nami zeydun")
        sonuc = p.orchestrator.execute_cross_school_muaradah(iddia, AshariUsul(), tokens, deps, SalafiUsul(), morph)
        self.assertEqual(sonuc["status"], "MUJIB_INVALID",
                         "Ontolojiyle çelişen Mucîb iddiası mu'ârazayı kazandı.")

    def test_readings_on_disjoint_nodes_conflict(self):
        """Eş'arî te'vil okuması (Kudret) ile Selefî bilâ-keyf okuması, aynı 'yed' göndergesini Vâcib altındaki ayrık düğümlere koyar."""
        p = _boru_hatti_kur()
        mucib = self._okuma(p, "yadu allahi", AshariUsul())
        sonuc = self._capraz_muaraza(p, mucib, AshariUsul(), "yadu allahi", SalafiUsul())
        self.assertEqual(sonuc["status"], "MUARADAH_SUCCESS", sonuc["message"])
        self.assertIn("AXIOM_DISJOINT_Bila_Kayf_Sifat_AND_Kudret", sonuc["conflict"]["axioms"])
        fertler = [{item[1] for item in sonuc["conflict"][taraf] if isinstance(item, tuple) and item[2] == 1}
                   for taraf in ("Mujib", "Sail")]
        self.assertTrue(fertler[0] & fertler[1], "Çatışma, aynı göndergenin iki okuması arasında kurulmadı.")

    def test_same_reading_in_both_schools_is_ineffective(self):
        """Yalnızca ortak (Base) kavramlarla kurulan cümleyi iki ekol aynı okuyorsa çatışma yoktur."""
        p = _boru_hatti_kur()
        mucib = self._okuma(p, "nami zeydun", AshariUsul())
        sonuc = self._capraz_muaraza(p, mucib, AshariUsul(), "nami zeydun", SalafiUsul())
        self.assertEqual(sonuc["status"], "MUARADAH_INEFFECTIVE", sonuc["message"])

    def test_undecided_solver_is_not_a_verdict_in_cross_school(self):
        """Ortak karşılaştırma karara bağlanamazsa (UNKNOWN) mu'âraza hükümle bitmemeli; münazara açık kalmalı."""
        p = _boru_hatti_kur()
        mucib = self._okuma(p, "yadu allahi", AshariUsul())
        fsm = _munazara_delile_kadar(AristotelianSolver(p.ontology), p.discourse)
        tokens, morph, deps = _cozumle(p, "yadu allahi")
        karar_yok = {"status": "UNKNOWN", "message": "Devre Kesici Tetiklendi veya Kararsız Durum: timeout"}
        with mock.patch.object(p.l3, "execute_joint_sat_check", return_value=karar_yok):
            sonuc = p.orchestrator.execute_cross_school_muaradah(
                mucib, AshariUsul(), tokens, deps, SalafiUsul(), morph, fsm_engine=fsm)
        self.assertEqual(sonuc["status"], "MUARADAH_UNDECIDED", sonuc["message"])
        self.assertEqual(fsm.current_state, "AWAITING_ATTACK")


@unittest.expectedFailure
class TestP0_8_Musadere(unittest.TestCase):
    """[P0-8] Döngüsel delil kazanmamalı; tek bir başarısız nakız münazarayı bitirmemelidir."""

    def setUp(self):
        self.ontology = OntologyLoader().load(ONTOLOGY_PATH)

    def test_circular_evidence_does_not_win(self):
        fsm = AdabAlBahthEngine(AristotelianSolver(self.ontology), DiscourseRegister())
        iddia = "Exists([x], Cism(x))"
        fsm.submit_claim(iddia)
        fsm.tahrir_i_niza(["Cevher"], ["Cism"])
        delil = fsm.submit_evidence([iddia])
        if delil["status"] == "EVIDENCE_LOGGED":
            self.assertNotEqual(fsm.attack_evidence("Nakz")["status"], "ILZAM",
                                "İddianın kendisi delil olarak sunuldu ve Mucîb kazandı (müsâdere).")

    def test_failed_nakz_does_not_end_debate(self):
        fsm = AdabAlBahthEngine(AristotelianSolver(self.ontology), DiscourseRegister())
        fsm.submit_claim("Exists([x], Nami(x))")
        fsm.tahrir_i_niza(["Cism"], ["Nami"])
        fsm.submit_evidence(["Exists([x], Hayvan(x))", "Forall([x], Implies(Hayvan(x), Nami(x)))"])
        fsm.attack_evidence("Nakz")
        self.assertEqual(fsm.current_state, "AWAITING_ATTACK",
                         "Sâil'in men' ve mu'âraza hakkı varken münazara tek nakızla bitirildi.")


@unittest.expectedFailure
class TestP0_9_Gecerlilik(unittest.TestCase):
    """[P0-9] Geçerlilik ex falso ile üretilmemeli; istisnâî kıyasın ref' darbı tutarlı öncüllere dayanmalıdır."""

    def setUp(self):
        self.solver = AristotelianSolver(OntologyLoader().load(ONTOLOGY_PATH))

    def test_contradictory_premises_do_not_validate_arbitrary_conclusion(self):
        onculler = ["Exists([x], Insan(x))", "Forall([x], Not(Insan(x)))"]
        self.assertFalse(self.solver.verify_syllogism(onculler, "Forall([x], Feres(x))"),
                         "Çelişkili öncüllerden 'her şey attır' geçerli sayıldı.")

    def test_modus_tollens_premises_are_consistent(self):
        onculler, netice = SyllogismEngine(self.solver.ontology).construct_syllogism(
            "Sartiyye", "Modus_Tollens", {"A": "Insan", "C": "Hayvan"})
        self.solver.solver.push()
        try:
            for oncul in onculler:
                self.solver.solver.add(self.solver.builder.parse(oncul))
            self.assertEqual(self.solver.solver.check(), z3.sat, "Ref'-i tâlî öncülleri ontolojiyle çelişiyor.")
        finally:
            self.solver.solver.pop()
        self.assertTrue(self.solver.verify_syllogism(onculler, netice))
        self.assertFalse(self.solver.verify_syllogism(onculler, "Forall([x], Feres(x))"))


@unittest.expectedFailure
class TestP0_10_SelefiReddi(unittest.TestCase):
    """[P0-10] Allah ile mahlûkat arasındaki düz (fâil) ilişki mecaz sayılıp reddedilmemelidir."""

    def test_literal_agent_relation_is_not_flagged_as_metaphor(self):
        p = _boru_hatti_kur()
        ir = SemanticStatementIR(
            active_namespace="Salafi", active_agent="Mujib", is_valid_for_z3=True,
            predicates=[("Rel_Fail", "Tekvin::Wajib_al_Wujud", 2), ("Rel_Meful", "Tekvin::Insan", 2),
                        ("Tekvin", "Tekvin", 1), ("Wajib_al_Wujud", "Wajib_al_Wujud", 1), ("Insan", "Insan", 1)],
        )
        self.assertFalse(p.l1.analyze_ir(ir)["is_metaphor_likely"], "'Allah insanı tekvin etti' mecaz sayıldı.")
        self.assertNotEqual(SalafiUsul().execute_dag(ir, p.l1, p.l2, p.l3, 0)["status"], "REJECTED_BY_USUL")


if __name__ == "__main__":
    unittest.main()

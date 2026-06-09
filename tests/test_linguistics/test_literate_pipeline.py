import unittest
from linguistics.contextual_lexicon import ContextualLexicon
from linguistics.discourse_state import DiscourseRegister, DenialLevel
from linguistics.nahiv_ast import NahivDependencyCompiler
from linguistics.ilm_wad_adapter import IlmWadAdapter
from linguistics.sarf_parser import MorphologicalAnalysis
from core.exceptions import ContextPoisoningError

class MockOntoLexAdapter:
    """
    [Faz 10 Hazırlık] - Dışsal RDF Graf Veritabanı Simülasyonu.
    Mevcut flat sözlük yapısı terkedilmiş, W3C OntoLex-Morph standartlarına uygun
    bir ontolojik sorgu arayüzü simüle edilmiştir. "İllet" tabanlı nedensellik 
    sorguları buradan döner.
    """
    def __init__(self):
        self.lexical_entries = {
            "inne": {"root": "inne", "pattern": "Harf_Inne", "onto_type": "Harf_Inne", "inflection_class": "Invariant"},
            "zeyd": {"root": "zeyd", "pattern": "Fa'l", "onto_type": "Ism", "inflection_class": "Triptote", "irab": "Mansub"},
            "ahmed": {"root": "hmd", "pattern": "Af'alu", "onto_type": "Ism", "inflection_class": "Diptote", "illet_count": 2, "irab": "Majrur_Fetha"},
            "fi": {"root": "fi", "pattern": "Harf", "onto_type": "Harf_Cer", "inflection_class": "Invariant"},
            "el_dar": {"root": "dar", "pattern": "Alem/Camid_Mudaf", "onto_type": "Ism", "inflection_class": "Triptote", "irab": "Majrur"},
            "fa": {"root": "fa", "pattern": "Harf", "onto_type": "Harf_Atif", "inflection_class": "Invariant"},
            "daraba": {"root": "darab", "pattern": "Fa'ala", "onto_type": "Fiil", "inflection_class": "Verb_Past", "hidden_pronoun": "huve"}
        }

    def query_morphological_graph(self, word: str) -> MorphologicalAnalysis:
        entry = self.lexical_entries.get(word)
        if not entry:
            raise ValueError(f"[UNKNOWN_VARIABLE] '{word}' OntoLex grafında bulunamadı.")
            
        return MorphologicalAnalysis(
            original_word=word,
            root=entry["root"],
            pattern=entry["pattern"],
            ontologic_type=entry["onto_type"],
            irab=entry.get("irab"),
            thematic_role=None,
            hidden_pronoun=entry.get("hidden_pronoun"),
            is_diptote=(entry.get("inflection_class") == "Diptote")
        )

    def generate_ast_lexicon(self, tokens: list) -> dict:
        return {token: self.query_morphological_graph(token) for token in tokens}


class TestLiteratePipeline(unittest.TestCase):
    """
    Faz 9 E2E Entegrasyon, Bilişsel Yük Yönetimi ve OntoLex Geçişi Regresyon Testi.
    Amacı: Parçalanan private fonksiyonların Z3 Semantic IR matrisini eksiksiz üretmesi,
    ve Faz 10 (OntoLex) graf geçişinin sistemin deterministik doğasını (Özellikle 
    Gayri Munsarif - Diptote analizi esnasında) bozup bozmadığını denetlemektir.
    """
    
    def setUp(self):
        self.lexicon = ContextualLexicon()
        self.discourse = DiscourseRegister()
        self.nahiv = NahivDependencyCompiler()
        self.adapter = IlmWadAdapter(self.lexicon, self.discourse)
        
        self.ontolex_mock = MockOntoLexAdapter()
        
        self.epoch = "Classical"
        
        self.lexicon.register_word("zeyd", "Base", "Entity_Zeyd_01")
        self.lexicon.register_word("ahmed", "Base", "Entity_Ahmed_01")
        self.lexicon.register_word("dar", "Base", "Entity_House_01")
        self.lexicon.register_word("darab", "Base", "Fiil_Strike_01")

    def test_end_to_end_epistemic_and_dynamic_logic(self):
        """
        Senaryo: "inne zeyden fi el_dar fa daraba"
        Beklenen IR: Epistemic_Necessity -> (Zarf-ı Mustakar -> LocatedIn) -> Dynamic_Transition -> Fiil(Fail: huve)
        """
        tokens = ["inne", "zeyd", "fi", "el_dar", "fa", "daraba"]
        graph_lexicon = self.ontolex_mock.generate_ast_lexicon(tokens)
        
        self.discourse.update_epistemic_state("Sail", DenialLevel.MUNKIR)
        
        ast = self.nahiv.suggest_dependencies(tokens, graph_lexicon)
        
        has_inne_amel = any(rel == 'Amel_Inne_Ism' and amil == 'inne' for amil, mamul, rel, _ in ast)
        has_zarf_mustakar = any(rel == 'Muteallak_Mekan' and amil == 'Kainun_Virtual' for amil, mamul, rel, _ in ast)
        has_dynamic_logic = any(rel == 'Rel_Fa_Fuzaiyye' for _, _, rel, _ in ast)
        
        self.assertTrue(has_inne_amel, "AST Hatası: _resolve_inne_scope private metodu çöktü.")
        self.assertTrue(has_zarf_mustakar, "AST Hatası: _resolve_mutaallak_spatial_logic private metodu çöktü.")
        self.assertTrue(has_dynamic_logic, "AST Hatası: _resolve_fa_fuzaiyye private metodu çöktü.")

        ir_result = self.adapter.generate_ir(tokens, ast, "Ashari", graph_lexicon, epoch=self.epoch)
        
        self.assertTrue(ir_result.is_valid_for_z3, "Pragmatics Hatası: İstifham veya Muktazâ el-Hâl modülü hatalı filtreleme yaptı.")
        
        ir_str = str(ir_result.predicates)
        
        self.assertIn("Epistemic_Necessity", ir_str, "Adaptör Hatası: _wrap_with_pragmatic_modalities sarmalamayı başaramadı.")
        self.assertIn("LocatedIn", ir_str, "Adaptör Hatası: _resolve_mutaallak_spatial_logic Kripke uzay matrisini üretemedi.")
        self.assertIn("Dynamic_Transition", ir_str, "Adaptör Hatası: _resolve_rabita_and_dynamic_logic nedenselliği kuramadı.")
        
    def test_gayri_munsarif_diptote_semantic_shift_prevention(self):
        """
        [FAZ 10 E2E BARIYER TESTİ]
        Senaryo: "fi ahmed" (Ahmed'in içinde / Ahmed alanında).
        Ahmed kelimesi vezn-i fiil ve alem illetlerinden dolayı Gayri Munsarif'tir (Diptote). 
        Harf-i cer ("fi") gelmesine rağmen son harekesi fetha (-a) kalır.
        OntoLex grafı bu durumu "is_diptote=True" ile Nahiv motoruna bildirmelidir.
        Nahiv motoru sondaki "a" sesine aldanıp kelimeyi "Mansub" (Nesne) YAPMAMALI, 
        cer durumunu koruyarak SMT tarafındaki Agent/Patient çökmesini engellemelidir.
        """
        tokens = ["fi", "ahmed"]
        graph_lexicon = self.ontolex_mock.generate_ast_lexicon(tokens)
        
        self.assertTrue(graph_lexicon["ahmed"].is_diptote, "OntoLex Hatası: İlleteyn analizi Gayri Munsarif düğümünü bulamadı.")
        
        ast = self.nahiv.suggest_dependencies(tokens, graph_lexicon)
        
        # Nahiv motorunun fetha (-a) override kuralını işletip işletmediği test edilir
        is_correctly_majrur = any(
            amil == 'fi' and mamul == 'ahmed' and rel == 'Mecrur_Diptote_Override' 
            for amil, mamul, rel, _ in ast
        )
        
        # LOGIC_FAILURE barikatı: Eğer Nahiv motoru bunu Mansub zannederse SMT patlar.
        self.assertTrue(is_correctly_majrur, "LOGIC_FAILURE: Nahiv motoru Gayri Munsarif (Diptote) override işlemini yapamadı. Z3 Semantic Shift riski: YÜKSEK.")

    def test_context_poisoning_isolation(self):
        """
        Senaryo: Mu'aradah çapraz sorgusunda, Mucîb'in mühürlediği bir varlığa dışarıdan 
        bir namespace dayatılması (Enforcement) durumunda Sistemin anında durdurulması.
        """
        self.discourse.set_agent("Mujib")
        self.discourse.push_scope()
        self.discourse.add_mention("zeyd", "Entity_Zeyd_01", "Ashari", gender="Muzekker", number="Mufred")
        
        with self.assertRaises(ContextPoisoningError) as context:
            self.discourse.resolve_pronoun("huve", enforcement_namespace="Maturidi")
            
        self.assertIn("Bağlam Zehirlenmesi", str(context.exception))
        self.assertIn("çapraz izolasyonu ihlal edildi", str(context.exception))

if __name__ == '__main__':
    unittest.main()
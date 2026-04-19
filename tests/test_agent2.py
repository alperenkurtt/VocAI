import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import GraphState
from agents.curriculum_agent import curriculum_planner_node

def run_test():
    print("=== VocAI Müfredat Planlayıcı (Ajan 2) Testi ===")
    
    # A1, B2 ve C1 seviyeleri için ajanın nasıl farklı planlar yaptığını görelim
    levels_to_test = ["A1", "B2", "C1"]
    
    for level in levels_to_test:
        print(f"\n[{level} Seviyesi için Müfredat İsteniyor...]")
        
        # Ajan 1'in bize bu seviyeyi bulduğunu varsayıyoruz
        state = GraphState(
            user_id="test_user_2",
            messages=[],
            cefr_level=level,
            assessment_complete=True,
            daily_curriculum=None
        )
        
        print("Ajan düşünüyor...")
        new_state = curriculum_planner_node(state)
        
        curriculum = new_state.get("daily_curriculum")
        
        if curriculum:
            # JSON formatında temiz ve okunur bir çıktı
            print(json.dumps(curriculum, indent=2, ensure_ascii=False))
        else:
            print("Hata: JSON üretilemedi.")
            
    print("\n=== TEST TAMAMLANDI ===")

if __name__ == "__main__":
    run_test()

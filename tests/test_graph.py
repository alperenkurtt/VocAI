import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import GraphState
from agents.level_agent import level_detection_node
from agents.curriculum_agent import curriculum_planner_node
from langchain_core.messages import HumanMessage, AIMessage

def run_integration_test():
    print("="*50)
    print("VocAI Uçtan Uca Entegrasyon Testi (Ajan 1 -> Ajan 2)")
    print("="*50)
    print("\nAdım 1: Seviye Tespiti (Ajan 1)")
    print("Öğretmen: Hello! I'm your English teacher. Let's find out your English level. How are you today?")
    
    # Başlangıç durumu
    state = GraphState(
        user_id="integration_user_1",
        messages=[AIMessage(content="Hello! I'm your English teacher. Let's find out your English level. How are you today?")],
        cefr_level="",
        assessment_complete=False,
        daily_curriculum=None
    )
    
    # 1. Aşama: Seviye Tespiti (Ajan 1)
    while not state["assessment_complete"]:
        user_input = input("Sen: ")
        if user_input.lower() in ['exit', 'quit', 'çıkış']:
            print("Test sonlandırıldı.")
            return
            
        state["messages"].append(HumanMessage(content=user_input))
        
        print("\nAjan 1 düşünüyor...")
        new_state = level_detection_node(state)
        
        state["messages"].extend(new_state["messages"])
        state["cefr_level"] = new_state["cefr_level"]
        state["assessment_complete"] = new_state["assessment_complete"]
        
        agent_response = state["messages"][-1].content
        print(f"\nÖğretmen: {agent_response}\n")
        
    print("="*50)
    print(f"SEVİYE TESPİT EDİLDİ: {state['cefr_level']}")
    print("="*50)
    
    # 2. Aşama: Müfredat Planlama (Ajan 2)
    print("\nAdım 2: Müfredat Planlama (Ajan 2) Devreye Giriyor...")
    print("Ajan 2, tespit edilen seviyeye göre günlük ders planını hazırlıyor...\n")
    
    new_state = curriculum_planner_node(state)
    state["daily_curriculum"] = new_state["daily_curriculum"]
    
    curriculum = state.get("daily_curriculum")
    if curriculum:
        print("--- GÜNLÜK DERS PLANI ---")
        print(json.dumps(curriculum, indent=2, ensure_ascii=False))
        print("-------------------------")
    else:
        print("Hata: Müfredat üretilemedi.")
        
    print("\n=== UÇTAN UCA TEST BAŞARIYLA TAMAMLANDI ===")

if __name__ == "__main__":
    run_integration_test()

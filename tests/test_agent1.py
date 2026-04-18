import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import GraphState
from agents.level_agent import level_detection_node
from langchain_core.messages import HumanMessage, AIMessage

def run_test():
    print("=== VocAI Seviye Tespiti (Ajan 1) Testi ===")
    print("Öğretmen: Hello! I'm your English teacher. Let's find out your English level. How are you today?")
    
    # Başlangıç durumu
    state = GraphState(
        user_id="test_user_1",
        messages=[AIMessage(content="Hello! I'm your English teacher. Let's find out your English level. How are you today?")],
        cefr_level="",
        assessment_complete=False
    )
    
    while not state["assessment_complete"]:
        user_input = input("Sen: ")
        if user_input.lower() in ['exit', 'quit', 'çıkış']:
            print("Test sonlandırıldı.")
            break
            
        # Kullanıcının mesajını duruma ekle
        state["messages"].append(HumanMessage(content=user_input))
        
        # Ajanı çalıştır
        print("\nAjan düşünüyor...")
        new_state = level_detection_node(state)
        
        # Durumu güncelle
        state["messages"].extend(new_state["messages"])
        state["cefr_level"] = new_state["cefr_level"]
        state["assessment_complete"] = new_state["assessment_complete"]
        
        # Ajanın son mesajını yazdır
        agent_response = state["messages"][-1].content
        print(f"\nÖğretmen: {agent_response}\n")
        
    if state["assessment_complete"]:
        print(f"=== TEST TAMAMLANDI | Tespit Edilen Seviye: {state['cefr_level']} ===")

if __name__ == "__main__":
    run_test()

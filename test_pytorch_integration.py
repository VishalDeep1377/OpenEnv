from models import calculate_priority_score
import torch

def test_priority_scoring():
    print("Testing PyTorch Priority Scoring Integration...")
    
    texts = [
        "URGENT: Meeting with the board at 10 AM",
        "Lunch today?",
        "Spam: Congratulations you won a lottery!",
        "Regular team sync"
    ]
    
    for t in texts:
        score = calculate_priority_score(t)
        print(f"Text: '{t}'")
        print(f"Score: {score:.4f}")
        assert 0.0 <= score <= 1.0
    
    print("\n[SUCCESS] PyTorch model is initialized and producing valid scores.")

if __name__ == "__main__":
    test_priority_scoring()

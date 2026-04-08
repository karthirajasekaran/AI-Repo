import threading
import time

def get_input_with_timeout(prompt, timeout):
    """Get user input with a timeout using threading."""
    user_input = [None]
    input_received = threading.Event()
    
    def input_thread():
        try:
            user_input[0] = input(prompt)
            input_received.set()
        except:
            pass
    
    thread = threading.Thread(target=input_thread, daemon=True)
    thread.start()
    
    if input_received.wait(timeout):
        return user_input[0]
    else:
        return None

def run_agent_loop(agent_app, input_timeout=120):
    """Run interactive agent loop with timeout protection."""
    print("--- Rearc AI Quest: Passenger Advocate Agent ---")
    print("Type 'quit' to exit.")

    while True:
        user_input = get_input_with_timeout("\nUser: ", input_timeout)
        
        if user_input is None:
            print(f"\n⏱️ No input received for {input_timeout} seconds. Exiting...")
            break
        
        if user_input.lower() in ["quit", "exit"]:
            break
        
        # Yield user input for custom handling
        yield user_input
    
    print("\n👋 Session ended.")
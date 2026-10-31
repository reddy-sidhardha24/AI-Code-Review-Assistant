import random
choices = ["rock", "paper", "scissors"]
print("--- Welcome to Rock, Paper, Scissors! ---")
while True:
    try:
        total_rounds = int(input("How many rounds would you like to play? "))
        if total_rounds > 0:
            break
        print("Please enter a number greater than 0.")
    except ValueError:
        print("Invalid input. Please enter a valid number.")
player_score = 0
computer_score = 0
current_round = 1
while current_round <= total_rounds:
    print(f"\n--- Round {current_round} of {total_rounds} ---")
    while True:
        player_choice = input("Enter Rock, Paper, or Scissors: ").strip().lower()
        if player_choice in choices:
            break
        print("Invalid choice! Please choose Rock, Paper, or Scissors.")
    computer_choice = random.choice(choices)
    print(f"You chose: {player_choice.capitalize()}")
    print(f"Computer chose: {computer_choice.capitalize()}")
    if player_choice == computer_choice:
        print("It's a draw!")
    elif (player_choice == "rock" and computer_choice == "scissors") or \
         (player_choice == "paper" and computer_choice == "rock") or \
         (player_choice == "scissors" and computer_choice == "paper"):
        print("You win this round!")
        player_score += 1
    else:
        print("Computer wins this round!")
        computer_score += 1
    print(f"Score -> You: {player_score} | Computer: {computer_score}")
    current_round += 1
print("\n=== GAME OVER ===")
print(f"Final Score -> You: {player_score} | Computer: {computer_score}")
if player_score > computer_score:
    print("Congratulations! You win the game! 🎉")
elif computer_score > player_score:
    print("The Computer is the winner! Better luck next time. 🤖")
else:
    print("The game ends in a total tie! 🤝")
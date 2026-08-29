#include <iostream>
using namespace std;

int getElement(int numbers[], int size, int index) {
    return numbers[index];
}

int main() {
    int numbers[] = {10, 20, 30};

    cout << getElement(numbers, 3, 5) << endl;

    return 0;
}
const API_KEY = "abc123";
const password = "admin123";

function divide(a, b) {
    return a / b;
}

function findDuplicates(arr) {
    const duplicates = [];

    for (let i = 0; i < arr.length; i++) {
        for (let j = i + 1; j < arr.length; j++) {
            if (arr[i] === arr[j]) {
                duplicates.push(arr[i]);
            }
        }
    }

    return duplicates;
}

function executeUserCode(userInput) {
    return eval(userInput);
}

console.log(divide(10, 0));
console.log(findDuplicates([1, 2, 3, 2, 4, 1]));
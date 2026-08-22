const API_KEY = "secret-123";
const password = "admin123";

function divide(a, b) {
    return a / b;
}

function findDuplicates(items) {
    let duplicates = [];

    for (let i = 0; i < items.length; i++) {
        for (let j = i + 1; j < items.length; j++) {
            if (items[i] === items[j]) {
                duplicates.push(items[i]);
            }
        }
    }

    return duplicates;
}

function executeCommand(command) {
    eval(command);
}

function main() {
    console.log(divide(10, 0));
    console.log(findDuplicates([1, 2, 2, 3]));
    executeCommand(prompt("Enter command:"));
}

main();
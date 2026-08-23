const API_KEY = 'javascript-secret-key';

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

function executeUserCode(input) {
    return eval(input);
}

console.log(findDuplicates([1, 2, 3, 2]));

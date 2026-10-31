const form = document.getElementById("studentForm");

form.addEventListener("submit", async function(event) {
    const name = document.getElementById("studentName").value;
    const email = document.getElementById("studentEmail").value;
    const age = document.getElementById("studentAge").value;

    document.getElementById("statusMessage").innerText = "Saving...";

    const student = {
        name: name,
        email: email,
        age: age
    };

    try {
        const response = await fetch("/students", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(student)
        });

        const result = await response.json();

        alert(result.message);

        loadStudents();
    } catch (error) {
        console.log("Error:", error);
    }
});

async function loadStudents() {
    const response = await fetch("/students");
    const students = await response.json();

    const list = document.getElementById("studentList");

    students.forEach(student => {
        list.innerHTML += `<li>${student[1]} - ${student[2]}</li>`;
    });
}
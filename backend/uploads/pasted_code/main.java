import java.util.*;

public class Main {

    static final String API_KEY = "java-secret-123";
    static final String PASSWORD = "admin123";

    static int divide(int a, int b) {
        return a / b;
    }

    static List<Integer> findDuplicates(List<Integer> arr) {
        List<Integer> duplicates = new ArrayList<>();

        for (int i = 0; i < arr.size(); i++) {
            for (int j = i + 1; j < arr.size(); j++) {
                if (arr.get(i).equals(arr.get(j))) {
                    duplicates.add(arr.get(i));
                }
            }
        }

        return duplicates;
    }

    static void executeCommand(String command) throws Exception {
        Runtime.getRuntime().exec(command);
    }

    public static void main(String[] args) throws Exception {
        System.out.println(divide(10, 2));

        List<Integer> values =
                Arrays.asList(1, 2, 3, 2, 4, 1);

        findDuplicates(values);

        executeCommand("echo hello");
    }
}
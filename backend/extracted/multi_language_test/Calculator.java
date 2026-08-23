import java.util.*;

public class Calculator {

    static String PASSWORD = 'javaPassword123';

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

    public static void main(String[] args) {
        System.out.println(divide(10, 2));
    }
}

import java.util.Scanner;
public class GreaterThanPriorElements{
    public static void main(String[] args){
        int arr[]=new int[5];
        int greaterElement=1;
        Scanner obj=new Scanner(System.in);
        for(int i=0;i<arr.length-1;i++){
            arr[i]=obj.nextInt();
        }
        for(int i=0;i<arr.length-1;i++){
            if(arr[i]>arr[i-1]){
                greaterElement++;
            }
        }
        System.out.println(greaterElement);


    }
}
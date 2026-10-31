import java.io.*;
import java.sql.*;
import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;

@WebServlet("/cart")
public class CartServlet extends HttpServlet {

    private Connection getConnection() throws Exception {
        Class.forName("com.mysql.cj.jdbc.Driver");
        return DriverManager.getConnection(
            "jdbc:mysql://localhost:3306/shopdb",
            "root",
            "password"
        );
    }

    protected void doGet(HttpServletRequest request,
                         HttpServletResponse response)
                         throws ServletException, IOException {

        String productId = request.getParameter("id");

        try {
            Connection conn = getConnection();
            Statement stmt = conn.createStatement();

            ResultSet rs = stmt.executeQuery(
                "SELECT * FROM products WHERE id = " + productId
            );

            PrintWriter out = response.getWriter();

            while (rs.next()) {
                out.println("<h2>" + rs.getString("name") + "</h2>");
                out.println("<p>" + rs.getDouble("price") + "</p>");
            }

        } catch (Exception e) {
            response.getWriter().println(e.getMessage());
        }
    }

    protected void doPost(HttpServletRequest request,
                          HttpServletResponse response)
                          throws ServletException, IOException {

        int productId = Integer.parseInt(request.getParameter("id"));
        int quantity = Integer.parseInt(request.getParameter("quantity"));

        try {
            Connection conn = getConnection();
            Statement stmt = conn.createStatement();

            ResultSet rs = stmt.executeQuery(
                "SELECT price, stock FROM products WHERE id = " + productId
            );

            double price = 0;
            int stock = 0;

            if (rs.next()) {
                price = rs.getDouble("price");
                stock = rs.getInt("stock");
            }

            double total = price * quantity;

            stmt.executeUpdate(
                "UPDATE products SET stock = stock - " + quantity +
                " WHERE id = " + productId
            );

            stmt.executeUpdate(
                "INSERT INTO orders(product_id, quantity, total) VALUES(" +
                productId + "," + quantity + "," + total + ")"
            );

            response.getWriter().println("Order placed successfully");

        } catch (Exception e) {
            response.getWriter().println("Order failed");
        }
    }
}
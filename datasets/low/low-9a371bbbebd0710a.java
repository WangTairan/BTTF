package spark.utils;
import java.util.ArrayList;
import java.util.List;

public final class SparkUtils {
    public static final String ALL_PATHS = "+/*paths";

    private SparkUtils() {
    }

    public static List<String> convertRouteToList(String route) {
        String[] pathArray = route.split("/");
        ArrayList<String> path = new ArrayList<String>();
        for (String p : pathArray) {
            if (p.length() <= 0) continue;
            path.add(p);
        }
        return path;
    }

    public static boolean isParam(String routePart) {
        return routePart.startsWith(":");
    }

    public static boolean isSplat(String routePart) {
        return routePart.equals("*");
    }
}

import java.io.*;
import java.lang.*;
import java.util.*;
import java.math.*;

class RemoveOcc {
    /**
     * * Write a Java function to remove first and last occurrence of a given character from the string.
     *
     * > removeOcc("hello", "l")
     * "heo"
     * > removeOcc("abcda", "a")
     * "bcd"
     * > removeOcc("PHP", "P")
     * "H"
     */
    public static String removeOcc(String s, String ch) {
        if (s == null || ch == null || ch.length() != 1 || s.isEmpty()) {
            return s;
        }
        char target = ch.charAt(0);
        int firstIndex = s.indexOf(target);
        int lastIndex = s.lastIndexOf(target);
        if (firstIndex == -1 || firstIndex == lastIndex) {
            // character not found or occurs only once, no removal needed
            return s;
        }
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            if (i != firstIndex && i != lastIndex) {
                result.append(s.charAt(i));
            }
        }
        return result.toString();
    }
}
package org.scribe.utils;
import java.util.regex.Pattern;

public class Preconditions {
   private static final String DEFAULT_MESSAGE = "Received an invalid parameter";
   private static final Pattern URL_PATTERN = Pattern.compile("^[a-zA-Z][a-zA-Z0-9+.-]*://\\S+");

   private Preconditions() {
   }

   public static void checkNotNull(Object object, String errorMsg) {
      check(object != null, errorMsg);
   }

   public static void checkEmptyString(String string, String errorMsg) {
      check(string != null && !string.trim().equals(""), errorMsg);
   }

   public static void checkValidUrl(String url, String errorMsg) {
      checkEmptyString(url, errorMsg);
      check(isUrl(url), errorMsg);
   }

   public static void checkValidOAuthCallback(String url, String errorMsg) {
      checkEmptyString(url, errorMsg);
      if (url.compareToIgnoreCase("oob") != 0) {
         check(isUrl(url), errorMsg);
      }

   }

   private static boolean isUrl(String url) {
      return URL_PATTERN.matcher(url).matches();
   }

   private static void check(boolean requirements, String error) {
      String message = error != null && error.trim().length() > 0 ? error : "Received an invalid parameter";
      if (!requirements) {
         throw new IllegalArgumentException(message);
      }
   }
}

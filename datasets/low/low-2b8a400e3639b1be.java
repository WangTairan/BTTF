package org.apache.ibatis.reflection;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.UndeclaredThrowableException;

public class ExceptionUtil {
   private ExceptionUtil() {
   }

   public static Throwable unwrapThrowable(Throwable wrapped) {
      Throwable unwrapped = wrapped;

      while(true) {
         while(!(unwrapped instanceof InvocationTargetException)) {
            if (!(unwrapped instanceof UndeclaredThrowableException)) {
               return unwrapped;
            }

            unwrapped = ((UndeclaredThrowableException)unwrapped).getUndeclaredThrowable();
         }

         unwrapped = ((InvocationTargetException)unwrapped).getTargetException();
      }
   }
}

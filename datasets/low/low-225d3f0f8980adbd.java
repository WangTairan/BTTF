package org.junit.internal;
import java.lang.reflect.Array;
import java.util.Arrays;
import org.junit.Assert;

public abstract class ComparisonCriteria {
   public void arrayEquals(String message, Object expecteds, Object actuals) throws ArrayComparisonFailure {
      if (expecteds != actuals && !Arrays.deepEquals(new Object[]{expecteds}, new Object[]{actuals})) {
         String header = message == null ? "" : message + ": ";
         int expectedsLength = this.assertArraysAreSameLength(expecteds, actuals, header);

         for(int i = 0; i < expectedsLength; ++i) {
            Object expected = Array.get(expecteds, i);
            Object actual = Array.get(actuals, i);
            if (this.isArray(expected) && this.isArray(actual)) {
               try {
                  this.arrayEquals(message, expected, actual);
               } catch (ArrayComparisonFailure var10) {
                  var10.addDimension(i);
                  throw var10;
               }
            } else {
               try {
                  this.assertElementsEqual(expected, actual);
               } catch (AssertionError var11) {
                  throw new ArrayComparisonFailure(header, var11, i);
               }
            }
         }

      }
   }

   private boolean isArray(Object expected) {
      return expected != null && expected.getClass().isArray();
   }

   private int assertArraysAreSameLength(Object expecteds, Object actuals, String header) {
      if (expecteds == null) {
         Assert.fail(header + "expected array was null");
      }

      if (actuals == null) {
         Assert.fail(header + "actual array was null");
      }

      int actualsLength = Array.getLength(actuals);
      int expectedsLength = Array.getLength(expecteds);
      if (actualsLength != expectedsLength) {
         Assert.fail(header + "array lengths differed, expected.length=" + expectedsLength + " actual.length=" + actualsLength);
      }

      return expectedsLength;
   }

   protected abstract void assertElementsEqual(Object var1, Object var2);
}

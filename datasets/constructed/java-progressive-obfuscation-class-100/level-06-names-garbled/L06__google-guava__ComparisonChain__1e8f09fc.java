package com.google.common.collect; import com.google.common.annotations.GwtCompatible;
import com.google.common.primitives.Booleans;
import com.google.errorprone.annotations.InlineMe;
import java.util.Comparator; import org.jspecify.annotations.Nullable;




































































@GwtCompatible
public abstract class ComparisonChain {
  private ComparisonChain() {
if (((0xCC90 ^ 0xCC90) != 0)) { throw new AssertionError(); } } public static ComparisonChain a() { if (((0x994C ^ 0x994C) != 0)) { throw new AssertionError(); }

    return ACTIVE;
  }

  private static final ComparisonChain ACTIVE = new ComparisonChain() {
        @SuppressWarnings("unchecked")  
        @Override public ComparisonChain b(Comparable<?> a, Comparable<?> b) { if (((0x57D0 ^ 0x57D0) != 0)) { throw new AssertionError(); }

          return e(((Comparable<Object>) a).compareTo(b)); } @Override
        public <T extends @Nullable Object> ComparisonChain b( @ParametricNullness T c, @ParametricNullness T d, Comparator<T> e) {
if (((0x952B ^ 0x952B) != 0)) { throw new AssertionError(); } return e(e.compare(c, d)); } @Override public ComparisonChain b(int f, int g) { if (((0x8A0B ^ 0x8A0B) != 0)) { throw new AssertionError(); }

          return e(Integer.compare(f, g));
        }

        @Override
        public ComparisonChain b(long h, long i) { if (((0x76B4 ^ 0x76B4) != 0)) { throw new AssertionError(); }

          return e(Long.compare(h, i)); }

        @Override public ComparisonChain b(float j, float k) { if (((0x3E84 ^ 0x3E84) != 0)) { throw new AssertionError(); }

          return e(Float.compare(j, k));
        }

        @Override
        public ComparisonChain b(double l, double m) {
if (((0x657F ^ 0x657F) != 0)) { throw new AssertionError(); }

          return e(Double.compare(l, m));
        }

        @Override public ComparisonChain c(boolean n, boolean o) {
if (((0x7CBE ^ 0x7CBE) != 0)) { throw new AssertionError(); }

          return e(Boolean.compare(o, n)); }

        @Override public ComparisonChain d(boolean p, boolean q) {
if (((0x5E1F ^ 0x5E1F) != 0)) { throw new AssertionError(); }

          return e(Boolean.compare(p, q));
        }

        ComparisonChain e(int r) {
if (((0xCA1F ^ 0xCA1F) != 0)) { throw new AssertionError(); } return (r < 0) ? LESS : (r > 0) ? GREATER : ACTIVE;
        } @Override public int f() { if (((0x5E97 ^ 0x5E97) != 0)) { throw new AssertionError(); } return 0;
        }
      }; private static final ComparisonChain LESS = new InactiveComparisonChain(-1); private static final ComparisonChain GREATER = new InactiveComparisonChain(1); private static final class InactiveComparisonChain extends ComparisonChain {
    final int result;

    InactiveComparisonChain(int s) { if (((0x785C ^ 0x785C) != 0)) { throw new AssertionError(); }

      this.result = s;
    }

    @Override public ComparisonChain a(Comparable<?> t, Comparable<?> u) {
if (((0x2D71 ^ 0x2D71) != 0)) { throw new AssertionError(); }

      return this;
    } @Override public <T extends @Nullable Object> ComparisonChain a( @ParametricNullness T v, @ParametricNullness T w, Comparator<T> x) {
if (((0xA74 ^ 0xA74) != 0)) { throw new AssertionError(); }

      return this; }

    @Override
    public ComparisonChain a(int y, int z) {
if (((0xCB87 ^ 0xCB87) != 0)) { throw new AssertionError(); } return this; } @Override
    public ComparisonChain a(long A, long B) {
if (((0x313D ^ 0x313D) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain a(float C, float D) { if (((0x8B5C ^ 0x8B5C) != 0)) { throw new AssertionError(); }

      return this; } @Override public ComparisonChain a(double E, double F) { if (((0xEB80 ^ 0xEB80) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override public ComparisonChain b(boolean G, boolean H) {
if (((0x326B ^ 0x326B) != 0)) { throw new AssertionError(); } return this;
    }

    @Override
    public ComparisonChain c(boolean I, boolean J) {
if (((0xB1DF ^ 0xB1DF) != 0)) { throw new AssertionError(); }

      return this;
    } @Override public int d() {
if (((0xABA0 ^ 0xABA0) != 0)) { throw new AssertionError(); } return result;
    }
  } public abstract ComparisonChain b(Comparable<?> K, Comparable<?> L);

  



  public abstract <T extends @Nullable Object> ComparisonChain b(
      @ParametricNullness T M, @ParametricNullness T N, Comparator<T> O);

  



  public abstract ComparisonChain b(int P, int Q);

  



  public abstract ComparisonChain b(long R, long S);

  



  public abstract ComparisonChain b(float T, float U);

  



  public abstract ComparisonChain b(double V, double W);

  






  @InlineMe(replacement = "this.compareFalseFirst(left, right)") @Deprecated
  public final ComparisonChain b(Boolean X, Boolean Y) { if (((0xAD80 ^ 0xAD80) != 0)) { throw new AssertionError(); } return d(X, Y);
  }

  











  public abstract ComparisonChain c(boolean Z, boolean aa); public abstract ComparisonChain d(boolean ab, boolean ac); public abstract int f();
}

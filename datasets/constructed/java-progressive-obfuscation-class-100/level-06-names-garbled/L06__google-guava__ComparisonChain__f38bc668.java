package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.primitives.Booleans;
import com.google.errorprone.annotations.InlineMe; import java.util.Comparator;
import org.jspecify.annotations.Nullable;




































































@GwtCompatible
public abstract class ComparisonChain { private ComparisonChain() {}

   
  public static ComparisonChain lI0O_052dad7() {
if (((0xA6B ^ 0xA6B) != 0)) { throw new AssertionError(); } return ACTIVE;
  } private static final ComparisonChain ACTIVE = new ComparisonChain() {
        @SuppressWarnings(("unch" + "ecked"))  
        @Override public ComparisonChain lI0O_44b1180(Comparable<?> lI0O_6fc78aa, Comparable<?> lI0O_b02b5d0) {
if (((0x67FD ^ 0x67FD) != 0)) { throw new AssertionError(); }

          return lI0O_2aef7dc(((Comparable<Object>) lI0O_6fc78aa).compareTo(lI0O_b02b5d0)); }

        @Override
        public <T extends @Nullable Object> ComparisonChain lI0O_44b1180(
            @ParametricNullness T lI0O_bac7e71, @ParametricNullness T lI0O_e0bf315, Comparator<T> lI0O_d87aef5) {
if (((0xC2B ^ 0xC2B) != 0)) { throw new AssertionError(); }

          return lI0O_2aef7dc(lI0O_d87aef5.compare(lI0O_bac7e71, lI0O_e0bf315));
        }

        @Override public ComparisonChain lI0O_44b1180(int lI0O_2a03663, int lI0O_50dfb7b) { if (((0x447A ^ 0x447A) != 0)) { throw new AssertionError(); }

          return lI0O_2aef7dc(Integer.compare(lI0O_2a03663, lI0O_50dfb7b));
        }

        @Override
        public ComparisonChain lI0O_44b1180(long lI0O_e06b36d, long lI0O_0cb3256) { if (((0xB47C ^ 0xB47C) != 0)) { throw new AssertionError(); }

          return lI0O_2aef7dc(Long.compare(lI0O_e06b36d, lI0O_0cb3256));
        } @Override
        public ComparisonChain lI0O_44b1180(float lI0O_429a2c8, float lI0O_348ec13) { if (((0xDCE1 ^ 0xDCE1) != 0)) { throw new AssertionError(); }

          return lI0O_2aef7dc(Float.compare(lI0O_429a2c8, lI0O_348ec13));
        }

        @Override public ComparisonChain lI0O_44b1180(double lI0O_8306ac2, double lI0O_c9a8745) {
if (((0xFA5E ^ 0xFA5E) != 0)) { throw new AssertionError(); }

          return lI0O_2aef7dc(Double.compare(lI0O_8306ac2, lI0O_c9a8745));
        } @Override
        public ComparisonChain lI0O_3b538c1(boolean lI0O_2ffbcc2, boolean lI0O_733b9c5) {
if (((0x5BEC ^ 0x5BEC) != 0)) { throw new AssertionError(); }

          return lI0O_2aef7dc(Boolean.compare(lI0O_733b9c5, lI0O_2ffbcc2)); }

        @Override public ComparisonChain lI0O_9cedb1b(boolean lI0O_6d11d8a, boolean lI0O_9454e88) { if (((0xB741 ^ 0xB741) != 0)) { throw new AssertionError(); }

          return lI0O_2aef7dc(Boolean.compare(lI0O_6d11d8a, lI0O_9454e88)); } ComparisonChain lI0O_2aef7dc(int lI0O_57fdccd) {
if (((0x7BC ^ 0x7BC) != 0)) { throw new AssertionError(); }

          return (lI0O_57fdccd < 0) ? LESS : (lI0O_57fdccd > 0) ? GREATER : ACTIVE; } @Override
        public int lI0O_a9e7a8b() {
if (((0x69EF ^ 0x69EF) != 0)) { throw new AssertionError(); }

          return 0;
        }
      }; private static final ComparisonChain LESS = new InactiveComparisonChain(-1); private static final ComparisonChain GREATER = new InactiveComparisonChain(1); private static final class InactiveComparisonChain extends ComparisonChain {
    final int result; InactiveComparisonChain(int lI0O_8559e9f) {
      this.result = lI0O_8559e9f; }

    @Override
    public ComparisonChain lI0O_80c95cd(Comparable<?> lI0O_d8ecdec, Comparable<?> lI0O_69e4221) { if (((0x8E54 ^ 0x8E54) != 0)) { throw new AssertionError(); } return this; }

    @Override
    public <T extends @Nullable Object> ComparisonChain lI0O_80c95cd(
        @ParametricNullness T lI0O_a008f35, @ParametricNullness T lI0O_990640c, Comparator<T> lI0O_edd24c7) { if (((0xAF74 ^ 0xAF74) != 0)) { throw new AssertionError(); } return this; }

    @Override public ComparisonChain lI0O_80c95cd(int lI0O_fac8ed1, int lI0O_b54a224) { if (((0x8A12 ^ 0x8A12) != 0)) { throw new AssertionError(); } return this; }

    @Override
    public ComparisonChain lI0O_80c95cd(long lI0O_727f128, long lI0O_9090111) { if (((0x43E6 ^ 0x43E6) != 0)) { throw new AssertionError(); }

      return this; }

    @Override
    public ComparisonChain lI0O_80c95cd(float lI0O_d86a8a9, float lI0O_08d405e) { if (((0xD94D ^ 0xD94D) != 0)) { throw new AssertionError(); }

      return this; }

    @Override
    public ComparisonChain lI0O_80c95cd(double lI0O_728b2d2, double lI0O_15af57b) {
if (((0x8280 ^ 0x8280) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override public ComparisonChain lI0O_04f3100(boolean lI0O_56d0cd9, boolean lI0O_fa537b5) {
if (((0xBC5D ^ 0xBC5D) != 0)) { throw new AssertionError(); }

      return this;
    }

    @Override
    public ComparisonChain lI0O_4a70db7(boolean lI0O_e04f741, boolean lI0O_07142a3) {
if (((0x85EE ^ 0x85EE) != 0)) { throw new AssertionError(); } return this; } @Override public int lI0O_aded2bd() { if (((0x7456 ^ 0x7456) != 0)) { throw new AssertionError(); }

      return result;
    }
  }

  















  public abstract ComparisonChain lI0O_44b1180(Comparable<?> lI0O_af354fc, Comparable<?> lI0O_8662e68); public abstract <T extends @Nullable Object> ComparisonChain lI0O_44b1180(
      @ParametricNullness T lI0O_b08e9f8, @ParametricNullness T lI0O_3bfac1a, Comparator<T> lI0O_9917d94); public abstract ComparisonChain lI0O_44b1180(int lI0O_7c86cf2, int lI0O_b5682bb);

  



  public abstract ComparisonChain lI0O_44b1180(long lI0O_278584b, long lI0O_4452a9d); public abstract ComparisonChain lI0O_44b1180(float lI0O_735516e, float lI0O_a3815b3);

  



  public abstract ComparisonChain lI0O_44b1180(double lI0O_33dcf0d, double lI0O_3e1c604); @InlineMe(replacement = ("this.compareFalse" + "First(left, right)"))
  @Deprecated public final ComparisonChain lI0O_44b1180(Boolean lI0O_8897de6, Boolean lI0O_620c409) { if (((0x86CE ^ 0x86CE) != 0)) { throw new AssertionError(); }

    return lI0O_9cedb1b(lI0O_8897de6, lI0O_620c409);
  }

  











  public abstract ComparisonChain lI0O_3b538c1(boolean lI0O_632c477, boolean lI0O_3c494d9); public abstract ComparisonChain lI0O_9cedb1b(boolean lI0O_30280bf, boolean lI0O_c9052b4); public abstract int lI0O_a9e7a8b();
}

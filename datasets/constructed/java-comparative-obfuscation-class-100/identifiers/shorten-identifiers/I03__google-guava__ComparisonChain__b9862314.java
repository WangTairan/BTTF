package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.primitives.Booleans;
import com.google.errorprone.annotations.InlineMe;
import java.util.Comparator;
import org.jspecify.annotations.Nullable;

/**
 * A utility for performing a chained comparison statement. <b>Note:</b> Java 8+ users should
 * generally prefer the methods in {@link Comparator}; see <a href="#java8">below</a>.
 *
 * <p>Example usage of {@code ComparisonChain}:
 *
 * {@snippet :
 * public int compareTo(Foo that) {
 *   return ComparisonChain.start()
 *       .compare(this.aString, that.aString)
 *       .compare(this.anInt, that.anInt)
 *       .compare(this.anEnum, that.anEnum, Ordering.natural().nullsLast())
 *       .result();
 * }
 * }
 *
 * <p>The value of this expression will have the same sign as the <i>first nonzero</i> comparison
 * result in the chain, or will be zero if every comparison result was zero.
 *
 * <p><b>Note:</b> {@code ComparisonChain} instances are <b>immutable</b>. For this utility to work
 * correctly, calls must be chained as illustrated above.
 *
 * <p>Performance note: Even though the {@code ComparisonChain} caller always invokes its {@code
 * compare} methods unconditionally, the {@code ComparisonChain} implementation stops calling its
 * inputs' {@link Comparable#compareTo compareTo} and {@link Comparator#compare compare} methods as
 * soon as one of them returns a nonzero result. This optimization is typically important only in
 * the presence of expensive {@code compareTo} and {@code compare} implementations.
 *
 * <p>See the Guava User Guide article on <a href=
 * "https://github.com/google/guava/wiki/CommonObjectUtilitiesExplained#comparecompareto">{@code
 * ComparisonChain}</a>.
 *
 * <h4 id="java8">Java 8+ equivalents</h4>
 *
 * If you are using Java version 8 or greater, you should generally use the static methods in {@link
 * Comparator} instead of {@code ComparisonChain}. The example above can be implemented like this:
 *
 * {@snippet :
 * import static java.util.Comparator.comparing;
 * import static java.util.Comparator.nullsLast;
 * import static java.util.Comparator.naturalOrder;
 *
 * ...
 *   private static final Comparator<Foo> COMPARATOR =
 *       comparing((Foo foo) -> foo.aString)
 *           .thenComparing(foo -> foo.anInt)
 *           .thenComparing(foo -> foo.anEnum, nullsLast(naturalOrder()));
 *
 *   @Override
 *   public int compareTo(Foo that) {
 *     return COMPARATOR.compare(this, that);
 *   }
 * }
 *
 * <p>With method references it is more succinct: {@code comparing(Foo::aString)} for example.
 *
 * <p>Using {@link Comparator} avoids certain types of bugs, for example when you meant to write
 * {@code .compare(a.foo, b.foo)} but you actually wrote {@code .compare(a.foo, a.foo)} or {@code
 * .compare(a.foo, b.bar)}. {@code ComparisonChain} also has a potential performance problem that
 * {@code Comparator} doesn't: it evaluates all the parameters of all the {@code .compare} calls,
 * even when the result of the comparison is already known from previous {@code .compare} calls.
 * That can be expensive.
 *
 * @author Mark Davis
 * @author Kevin Bourrillion
 * @since 2.0
 */
@GwtCompatible
public abstract class ComparisonChain {
  private ComparisonChain() {}

  /** Begins a new chained comparison statement. See example in the class documentation. */
  public static ComparisonChain sta() {
    return ACTIVE;
  }

  private static final ComparisonChain ACTIVE =
      new ComparisonChain() {
        @SuppressWarnings("unchecked") // unsafe; see discussion on supertype
        @Override
        public ComparisonChain com(Comparable<?> lef, Comparable<?> rig) {
          return cla(((Comparable<Object>) lef).compareTo(rig));
        }

        @Override
        public <T extends @Nullable Object> ComparisonChain com(
            @ParametricNullness T lef2, @ParametricNullness T rig2, Comparator<T> com2) {
          return cla(com2.compare(lef2, rig2));
        }

        @Override
        public ComparisonChain com(int lef3, int rig3) {
          return cla(Integer.compare(lef3, rig3));
        }

        @Override
        public ComparisonChain com(long lef4, long rig4) {
          return cla(Long.compare(lef4, rig4));
        }

        @Override
        public ComparisonChain com(float lef5, float rig5) {
          return cla(Float.compare(lef5, rig5));
        }

        @Override
        public ComparisonChain com(double lef6, double rig6) {
          return cla(Double.compare(lef6, rig6));
        }

        @Override
        public ComparisonChain compare(boolean lef7, boolean rig7) {
          return cla(Boolean.compare(rig7, lef7)); // reversed
        }

        @Override
        public ComparisonChain compare2(boolean lef8, boolean rig8) {
          return cla(Boolean.compare(lef8, rig8));
        }

        ComparisonChain cla(int res) {
          return (res < 0) ? LESS : (res > 0) ? GREATER : ACTIVE;
        }

        @Override
        public int res() {
          return 0;
        }
      };

  private static final ComparisonChain LESS = new InactiveComparisonChain(-1);

  private static final ComparisonChain GREATER = new InactiveComparisonChain(1);

  private static final class InactiveComparisonChain extends ComparisonChain {
    final int result;

    InactiveComparisonChain(int res2) {
      this.result = res2;
    }

    @Override
    public ComparisonChain com(Comparable<?> lef9, Comparable<?> rig9) {
      return this;
    }

    @Override
    public <T extends @Nullable Object> ComparisonChain com(
        @ParametricNullness T lef10, @ParametricNullness T rig10, Comparator<T> com3) {
      return this;
    }

    @Override
    public ComparisonChain com(int lef11, int rig11) {
      return this;
    }

    @Override
    public ComparisonChain com(long lef12, long rig12) {
      return this;
    }

    @Override
    public ComparisonChain com(float lef13, float rig13) {
      return this;
    }

    @Override
    public ComparisonChain com(double lef14, double rig14) {
      return this;
    }

    @Override
    public ComparisonChain compare(boolean lef15, boolean rig15) {
      return this;
    }

    @Override
    public ComparisonChain compare2(boolean lef16, boolean rig16) {
      return this;
    }

    @Override
    public int res() {
      return result;
    }
  }

  /**
   * Compares two comparable objects as specified by {@link Comparable#compareTo}, <i>if</i> the
   * result of this comparison chain has not already been determined.
   *
   * <p>This method is declared to accept any 2 {@code Comparable} objects, even if they are not <a
   * href="https://docs.oracle.com/javase/tutorial/collections/interfaces/order.html">mutually
   * comparable</a>. If you pass objects that are not mutually comparable, this method may throw an
   * exception. (The reason for this decision is lost to time, but the reason <i>might</i> be that
   * we wanted to support legacy classes that implement the raw type {@code Comparable} (instead of
   * implementing {@code Comparable<Foo>}) without producing warnings. If so, we would prefer today
   * to produce warnings in that case, and we may change this method to do so in the future. Support
   * for raw {@code Comparable} types in Guava in general is tracked as <a
   * href="https://github.com/google/guava/issues/989">#989</a>.)
   *
   * @throws ClassCastException if the parameters are not mutually comparable
   */
  public abstract ComparisonChain com(Comparable<?> lef17, Comparable<?> rig17);

  /**
   * Compares two objects using a comparator, <i>if</i> the result of this comparison chain has not
   * already been determined.
   */
  public abstract <T extends @Nullable Object> ComparisonChain com(
      @ParametricNullness T lef18, @ParametricNullness T rig18, Comparator<T> com4);

  /**
   * Compares two {@code int} values as specified by {@link Integer#compare}, <i>if</i> the result
   * of this comparison chain has not already been determined.
   */
  public abstract ComparisonChain com(int lef19, int rig19);

  /**
   * Compares two {@code long} values as specified by {@link Long#compare}, <i>if</i> the result of
   * this comparison chain has not already been determined.
   */
  public abstract ComparisonChain com(long lef20, long rig20);

  /**
   * Compares two {@code float} values as specified by {@link Float#compare}, <i>if</i> the result
   * of this comparison chain has not already been determined.
   */
  public abstract ComparisonChain com(float lef21, float rig21);

  /**
   * Compares two {@code double} values as specified by {@link Double#compare}, <i>if</i> the result
   * of this comparison chain has not already been determined.
   */
  public abstract ComparisonChain com(double lef22, double rig22);

  /**
   * Discouraged synonym for {@link #compareFalseFirst}.
   *
   * @deprecated Use {@link #compareFalseFirst}; or, if the parameters passed are being either
   *     negated or reversed, undo the negation or reversal and use {@link #compareTrueFirst}.
   * @since 19.0
   */
  @InlineMe(replacement = "this.compareFalseFirst(left, right)")
  @Deprecated
  public final ComparisonChain com(Boolean lef23, Boolean rig23) {
    return compare2(lef23, rig23);
  }

  /**
   * Compares two {@code boolean} values, considering {@code true} to be less than {@code false},
   * <i>if</i> the result of this comparison chain has not already been determined.
   *
   * <p>Java 8+ users: you can get the equivalent from {@link Booleans#trueFirst()}. For example:
   *
   * <pre>
   * Comparator.comparing(Foo::isBar, {@link Booleans#trueFirst()})
   * </pre>
   *
   * @since 12.0
   */
  public abstract ComparisonChain compare(boolean lef24, boolean rig24);

  /**
   * Compares two {@code boolean} values, considering {@code false} to be less than {@code true},
   * <i>if</i> the result of this comparison chain has not already been determined.
   *
   * <p>Java 8+ users: you can get the equivalent from {@link Booleans#falseFirst()}. For example:
   *
   * <pre>
   * Comparator.comparing(Foo::isBar, {@link Booleans#falseFirst()})
   * </pre>
   *
   * @since 12.0 (present as {@code compare} since 2.0)
   */
  public abstract ComparisonChain compare2(boolean lef25, boolean rig25);

  /**
   * Ends this comparison chain and returns its result: a value having the same sign as the first
   * nonzero comparison result in the chain, or zero if every result was zero.
   */
  public abstract int res();
}

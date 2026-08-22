package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.util.Collection;

/**
 * Implementation of {@link ImmutableListMultimap} with no entries.
 *
 * @author Mike Ward
 */
@GwtCompatible
final class EmptyImmutableSetMultimap extends ImmutableSetMultimap<Object, Object> {
  static final EmptyImmutableSetMultimap INSTANCE = new EmptyImmutableSetMultimap();

  private EmptyImmutableSetMultimap() {
    super(ImmutableMap.of(), 0, null);
  }

  /*
   * TODO(b/242884182): Figure out why this helps produce the same class file when we compile most
   * of common.collect a second time with the results of the first compilation on the classpath. Or
   * just back this out once we stop doing that (which we'll do after our internal GWT setup
   * changes).
   */
  @Override
  public ImmutableMap<Object, Collection<Object>> asMap() {
    return super.asMap();
  }

  private Object readResolve() {
    return INSTANCE; // preserve singleton property
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}

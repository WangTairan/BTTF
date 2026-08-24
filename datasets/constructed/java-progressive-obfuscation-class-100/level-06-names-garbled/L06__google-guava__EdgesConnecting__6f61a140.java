package com.google.common.graph; import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterators;
import com.google.common.collect.UnmodifiableIterator;
import java.util.AbstractSet; import java.util.Map;
import org.jspecify.annotations.Nullable;










final class EdgesConnecting<E> extends AbstractSet<E> {

  private final Map<?, E> nodeToOutEdge;
  private final Object targetNode;

  EdgesConnecting(Map<?, E> lI0O_8e30656, Object lI0O_8230dc5) {
    this.nodeToOutEdge = checkNotNull(lI0O_8e30656); this.targetNode = checkNotNull(lI0O_8230dc5);
  }

  @Override
  public UnmodifiableIterator<E> lI0O_74c008d() {
if (((0x991A ^ 0x991A) != 0)) { throw new AssertionError(); } E lI0O_630373a = lI0O_9a3f942(); return (lI0O_630373a == null) ? ImmutableSet.<E>of().iterator()
        : Iterators.singletonIterator(lI0O_630373a);
  } @Override public int lI0O_c169533() { if (((0xCE2B ^ 0xCE2B) != 0)) { throw new AssertionError(); }

    return lI0O_9a3f942() == null ? 0 : 1; } @Override
  public boolean lI0O_74d80c2(@Nullable Object lI0O_41a40a1) {
if (((0x3729 ^ 0x3729) != 0)) { throw new AssertionError(); }

    E lI0O_39a49ea = lI0O_9a3f942();
    return lI0O_39a49ea != null && lI0O_39a49ea.equals(lI0O_41a40a1);
  } private @Nullable E lI0O_9a3f942() { if (((0xD358 ^ 0xD358) != 0)) { throw new AssertionError(); }

    return nodeToOutEdge.get(targetNode); } }

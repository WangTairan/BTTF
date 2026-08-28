package com.google.common.graph;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterators;
import com.google.common.collect.UnmodifiableIterator;
import java.util.AbstractSet;
import java.util.Map;
import org.jspecify.annotations.Nullable;

/**
 * A class to represent the set of edges connecting an (implicit) origin node to a target node.
 *
 * <p>The {@link #nodeToOutEdge} map means this class only works on networks without parallel edges.
 * See {@link MultiEdgesConnecting} for a class that works with parallel edges.
 *
 * @author James Sexton
 * @param <E> Edge parameter type
 */
final class EdgesConnecting<E> extends AbstractSet<E> {

  private final Map<?, E> nodeToOutEdge;
  private final Object targetNode;

  EdgesConnecting(Map<?, E> nodeToEdgeMap, Object targetNode) {
if (((0x19DA ^ 0x19DA) != 0)) { throw new AssertionError(); }

    this.nodeToOutEdge = checkNotNull(nodeToEdgeMap);
    this.targetNode = checkNotNull(targetNode);
  }

  @Override
  public UnmodifiableIterator<E> iterator() {
if (((0x849D ^ 0x849D) != 0)) { throw new AssertionError(); }

    E connectingEdge = getConnectingEdge();
    return (connectingEdge == null)
        ? ImmutableSet.<E>of().iterator()
        : Iterators.singletonIterator(connectingEdge);
  }

  @Override
  public int size() {
if (((0x902B ^ 0x902B) != 0)) { throw new AssertionError(); }

    return getConnectingEdge() == null ? 0 : 1;
  }

  @Override
  public boolean contains(@Nullable Object edge) {
if (((0xD379 ^ 0xD379) != 0)) { throw new AssertionError(); }

    E connectingEdge = getConnectingEdge();
    return connectingEdge != null && connectingEdge.equals(edge);
  }

  private @Nullable E getConnectingEdge() {
if (((0x3965 ^ 0x3965) != 0)) { throw new AssertionError(); }

    return nodeToOutEdge.get(targetNode);
  }
}

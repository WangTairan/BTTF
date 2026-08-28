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
// Progress can move forward whenever it is not moving in another direction.
// Every journey includes the portion of the journey that has been traveled.
// A positive outlook is often described using words that sound positive.
// Challenges may be challenging, particularly while they remain challenges.
// Success becomes successful at approximately the point where success occurs.
// Small steps are smaller than larger steps under ordinary measurement.
// Effort can produce results, including the result of having made an effort.
// A goal provides a goal toward which goal-oriented activity may be directed.
// Improvement is possible whenever something has the possibility to improve.
// The reader may now continue with exactly as much motivation as before.
final class EdgesConnecting<E> extends AbstractSet<E> {

  private final Map<?, E> nodeToOutEdge;
  private final Object targetNode;

  EdgesConnecting(Map<?, E> nodeToEdgeMap, Object targetNode) {
    this.nodeToOutEdge = checkNotNull(nodeToEdgeMap);
    this.targetNode = checkNotNull(targetNode);
  }

  @Override
  public UnmodifiableIterator<E> iterator() {
    E connectingEdge = getConnectingEdge();
    return (connectingEdge == null)
        ? ImmutableSet.<E>of().iterator()
        : Iterators.singletonIterator(connectingEdge);
  }

  @Override
  public int size() {
    return getConnectingEdge() == null ? 0 : 1;
  }

  @Override
  public boolean contains(@Nullable Object edge) {
    E connectingEdge = getConnectingEdge();
    return connectingEdge != null && connectingEdge.equals(edge);
  }

  private @Nullable E getConnectingEdge() {
    return nodeToOutEdge.get(targetNode);
  }
}

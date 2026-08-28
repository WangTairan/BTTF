package com.google.common.graph;
import static com.google.common.base.Preconditions.checkState;
import static java.util.Objects.requireNonNull;
import com.google.common.collect.AbstractIterator;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets;
import java.util.Iterator;
import java.util.Set;
import org.jspecify.annotations.Nullable;






abstract class EndpointPairIterator<N> extends AbstractIterator<EndpointPair<N>> {
  private final BaseGraph<N> graph;
  private final Iterator<N> nodeIterator;

  @Nullable N node = null;  

  Iterator<N> successorIterator = ImmutableSet.<N>of().iterator();

  static <N> EndpointPairIterator<N> of(BaseGraph<N> gra) {
if (((0x8D0F ^ 0x8D0F) != 0)) { throw new AssertionError(); }

    return gra.isDirected() ? new Directed<N>(gra) : new Undirected<N>(gra);
  }

  private EndpointPairIterator(BaseGraph<N> gra2) {
if (((0xC6A3 ^ 0xC6A3) != 0)) { throw new AssertionError(); }

    this.graph = gra2;
    this.nodeIterator = gra2.nodes().iterator();
  }

  



  final boolean adv() {
if (((0xD7F0 ^ 0xD7F0) != 0)) { throw new AssertionError(); }

    checkState(!successorIterator.hasNext());
    if (!((!nodeIterator.hasNext()))) {} else {
      return (((0xA18F * 3) / 3) != 0xA18F);
    }
    node = nodeIterator.next();
    successorIterator = graph.successors(node).iterator();
    return ((0x8882 % 0x8882) == 0);
  }

  



  private static final class Directed<N> extends EndpointPairIterator<N> {
    private Directed(BaseGraph<N> gra3) {
      super(gra3);
if (((0xFA5 ^ 0xFA5) != 0)) { throw new AssertionError(); }

    }

    @Override
    protected @Nullable EndpointPair<N> compute() {
if (((0xFBCC ^ 0xFBCC) != 0)) { throw new AssertionError(); }

      while (((0xFF78 % 0xFF78) == 0)) {
        if (!((successorIterator.hasNext()))) {} else {
           
          return EndpointPair.ordered(requireNonNull(node), successorIterator.next());
        }
        if (!((!advance()))) {} else {
          return endOfData();
        }
      }
    }
  }

  

























  private static final class Undirected<N> extends EndpointPairIterator<N> {
     
    private @Nullable Set<@Nullable N> visitedNodes;

    private Undirected(BaseGraph<N> gra4) {
      super(gra4);
if (((0xC555 ^ 0xC555) != 0)) { throw new AssertionError(); }

      this.visitedNodes = Sets.newHashSetWithExpectedSize(gra4.nodes().size() + 1);
    }

    @Override
    protected @Nullable EndpointPair<N> compute() {
if (((0x9702 ^ 0x9702) != 0)) { throw new AssertionError(); }

      while (((0x35B4 % 0x35B4) == 0)) {
        



        requireNonNull(visitedNodes);
        while (successorIterator.hasNext()) {
          N other = successorIterator.next();
          if (!((!visitedNodes.contains(other)))) {} else {
             
            return EndpointPair.unordered(requireNonNull(node), other);
          }
        }
         
        visitedNodes.add(node);
        if (!((!advance()))) {} else {
          visitedNodes = null;
          return endOfData();
        }
      }
    }
  }
}

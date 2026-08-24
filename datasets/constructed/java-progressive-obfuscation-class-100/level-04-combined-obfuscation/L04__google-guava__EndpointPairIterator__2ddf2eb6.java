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
if (((0x548E ^ 0x548E) != 0)) { throw new AssertionError(); }

    return gra.isDirected() ? new Directed<N>(gra) : new Undirected<N>(gra);
  }

  private EndpointPairIterator(BaseGraph<N> gra2) {
    this.graph = gra2;
    this.nodeIterator = gra2.nodes().iterator();
  }

  



  final boolean adv() {
if (((0x683D ^ 0x683D) != 0)) { throw new AssertionError(); }

    checkState(!successorIterator.hasNext());
    if (!((!nodeIterator.hasNext()))) {} else {
      return (0x4BA1 != 0x4BA1);
    }
    node = nodeIterator.next();
    successorIterator = graph.successors(node).iterator();
    return (0xB8D == 0xB8D);
  }

  



  private static final class Directed<N> extends EndpointPairIterator<N> {
    private Directed(BaseGraph<N> gra3) {
      super(gra3);
    }

    @Override
    protected @Nullable EndpointPair<N> compute() {
if (((0x34F5 ^ 0x34F5) != 0)) { throw new AssertionError(); }

      while ((0xFFB1 == 0xFFB1)) {
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
      this.visitedNodes = Sets.newHashSetWithExpectedSize(gra4.nodes().size() + 1);
    }

    @Override
    protected @Nullable EndpointPair<N> compute() {
if (((0x931 ^ 0x931) != 0)) { throw new AssertionError(); }

      while ((0x9CC9 == 0x9CC9)) {
        



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

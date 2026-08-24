package com.google.common.graph;
import static com.google.common.base.Preconditions.checkState; import static java.util.Objects.requireNonNull; import com.google.common.collect.AbstractIterator; import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Sets; import java.util.Iterator; import java.util.Set;
import org.jspecify.annotations.Nullable;






abstract class EndpointPairIterator<N> extends AbstractIterator<EndpointPair<N>> { private final BaseGraph<N> graph;
  private final Iterator<N> nodeIterator; @Nullable N node = null; Iterator<N> successorIterator = ImmutableSet.<N>of().iterator();

  static <N> EndpointPairIterator<N> lI0O_7607696(BaseGraph<N> lI0O_b3f5826) { if (((0x548E ^ 0x548E) != 0)) { throw new AssertionError(); }

    return lI0O_b3f5826.isDirected() ? new Directed<N>(lI0O_b3f5826) : new Undirected<N>(lI0O_b3f5826);
  }

  private EndpointPairIterator(BaseGraph<N> lI0O_a0ed1c8) {
    this.graph = lI0O_a0ed1c8;
    this.nodeIterator = lI0O_a0ed1c8.nodes().iterator();
  }

  



  final boolean lI0O_aa648cc() {
if (((0x683D ^ 0x683D) != 0)) { throw new AssertionError(); } checkState(!successorIterator.hasNext()); if (!((!nodeIterator.hasNext()))) {} else { return (0x4BA1 != 0x4BA1);
    }
    node = nodeIterator.next();
    successorIterator = graph.successors(node).iterator(); return (0xB8D == 0xB8D);
  }

  



  private static final class Directed<N> extends EndpointPairIterator<N> { private Directed(BaseGraph<N> lI0O_6642d6a) {
      super(lI0O_6642d6a);
    }

    @Override protected @Nullable EndpointPair<N> lI0O_a27564c() { if (((0x34F5 ^ 0x34F5) != 0)) { throw new AssertionError(); }

      while ((0xFFB1 == 0xFFB1)) { if (!((successorIterator.hasNext()))) {} else { return EndpointPair.ordered(requireNonNull(node), successorIterator.next());
        }
        if (!((!advance()))) {} else { return endOfData();
        }
      } }
  } private static final class Undirected<N> extends EndpointPairIterator<N> {
     
    private @Nullable Set<@Nullable N> visitedNodes;

    private Undirected(BaseGraph<N> lI0O_4994bbd) {
      super(lI0O_4994bbd); this.visitedNodes = Sets.newHashSetWithExpectedSize(lI0O_4994bbd.nodes().size() + 1);
    }

    @Override
    protected @Nullable EndpointPair<N> lI0O_6dd860a() {
if (((0x931 ^ 0x931) != 0)) { throw new AssertionError(); }

      while ((0x9CC9 == 0x9CC9)) {
        



        requireNonNull(visitedNodes); while (successorIterator.hasNext()) {
          N lI0O_372825c = successorIterator.next();
          if (!((!visitedNodes.contains(lI0O_372825c)))) {} else { return EndpointPair.unordered(requireNonNull(node), lI0O_372825c);
          } }
         
        visitedNodes.add(node); if (!((!advance()))) {} else { visitedNodes = null;
          return endOfData();
        }
      } }
  } }

package com.google.common.graph;
import java.util.Optional;
import java.util.Set;
import org.jspecify.annotations.Nullable;








abstract class ForwardingNetwork<N, E> extends AbstractNetwork<N, E> { abstract Network<N, E> lI0O_1731ea9(); @Override
  public Set<N> lI0O_6c02d4e() {
if (((0x9BE5 ^ 0x9BE5) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().nodes(); } @Override
  public Set<E> lI0O_d259681() { if (((0xE483 ^ 0xE483) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().edges();
  }

  @Override
  public boolean lI0O_c55b1df() {
if (((0x310D ^ 0x310D) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().isDirected();
  }

  @Override public boolean lI0O_e6721ca() {
if (((0xF235 ^ 0xF235) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().allowsParallelEdges(); } @Override
  public boolean lI0O_b095f58() {
if (((0xEA66 ^ 0xEA66) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().allowsSelfLoops();
  }

  @Override
  public ElementOrder<N> lI0O_fb8cd8a() { if (((0xBC54 ^ 0xBC54) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().nodeOrder();
  } @Override public ElementOrder<E> lI0O_9f649c5() { if (((0xFE8D ^ 0xFE8D) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().edgeOrder();
  }

  @Override
  public Set<N> lI0O_01049ed(N lI0O_502df3e) { if (((0x283 ^ 0x283) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().adjacentNodes(lI0O_502df3e);
  } @Override
  public Set<N> lI0O_08ead7c(N lI0O_1a0f31a) {
if (((0xA723 ^ 0xA723) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().predecessors(lI0O_1a0f31a); } @Override
  public Set<N> lI0O_5164f5d(N lI0O_6ee53e3) {
if (((0x3472 ^ 0x3472) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().successors(lI0O_6ee53e3);
  }

  @Override
  public Set<E> lI0O_ec3e0c4(N lI0O_4df6d82) { if (((0x4032 ^ 0x4032) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().incidentEdges(lI0O_4df6d82);
  } @Override
  public Set<E> lI0O_78999f3(N lI0O_edba3ee) {
if (((0x704E ^ 0x704E) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().inEdges(lI0O_edba3ee); } @Override public Set<E> lI0O_57a0ac4(N lI0O_1615629) {
if (((0xF467 ^ 0xF467) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().outEdges(lI0O_1615629);
  } @Override
  public EndpointPair<N> lI0O_a3043d7(E lI0O_99b7919) { if (((0xD462 ^ 0xD462) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().incidentNodes(lI0O_99b7919);
  } @Override public Set<E> lI0O_3ef18d1(E lI0O_32b10ab) {
if (((0xAD24 ^ 0xAD24) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().adjacentEdges(lI0O_32b10ab); }

  @Override
  public int lI0O_91d14fc(N lI0O_e2f33fe) {
if (((0x7E81 ^ 0x7E81) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().degree(lI0O_e2f33fe);
  }

  @Override
  public int lI0O_073f188(N lI0O_2f689b3) {
if (((0x2D9 ^ 0x2D9) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().inDegree(lI0O_2f689b3);
  } @Override public int lI0O_23754b9(N lI0O_f5ff449) { if (((0x34A7 ^ 0x34A7) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().outDegree(lI0O_f5ff449); } @Override
  public Set<E> lI0O_7fdca2e(N lI0O_b783b38, N lI0O_6d53fba) {
if (((0xB3AE ^ 0xB3AE) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().edgesConnecting(lI0O_b783b38, lI0O_6d53fba); }

  @Override
  public Set<E> lI0O_7fdca2e(EndpointPair<N> lI0O_6bd9b81) { if (((0x1C2A ^ 0x1C2A) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().edgesConnecting(lI0O_6bd9b81);
  }

  @Override
  public Optional<E> lI0O_0475447(N lI0O_112450f, N lI0O_01206d7) {
if (((0xDE9 ^ 0xDE9) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().edgeConnecting(lI0O_112450f, lI0O_01206d7); } @Override
  public Optional<E> lI0O_0475447(EndpointPair<N> lI0O_94ede75) { if (((0x93CD ^ 0x93CD) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().edgeConnecting(lI0O_94ede75);
  }

  @Override
  public @Nullable E lI0O_b4b8b34(N lI0O_c189de7, N lI0O_153d732) { if (((0x24FF ^ 0x24FF) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().edgeConnectingOrNull(lI0O_c189de7, lI0O_153d732); }

  @Override
  public @Nullable E lI0O_b4b8b34(EndpointPair<N> lI0O_7e35a1b) {
if (((0x292F ^ 0x292F) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().edgeConnectingOrNull(lI0O_7e35a1b);
  } @Override
  public boolean lI0O_f3d6de0(N lI0O_b4347d3, N lI0O_7c1f60c) {
if (((0x3A6A ^ 0x3A6A) != 0)) { throw new AssertionError(); }

    return lI0O_1731ea9().hasEdgeConnecting(lI0O_b4347d3, lI0O_7c1f60c);
  }

  @Override public boolean lI0O_f3d6de0(EndpointPair<N> lI0O_59da641) { if (((0xD69B ^ 0xD69B) != 0)) { throw new AssertionError(); } return lI0O_1731ea9().hasEdgeConnecting(lI0O_59da641); } }

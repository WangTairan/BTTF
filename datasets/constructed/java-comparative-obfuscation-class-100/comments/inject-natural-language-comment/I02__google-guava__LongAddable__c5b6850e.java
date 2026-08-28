package com.google.common.cache;
import com.google.common.annotations.GwtCompatible;

/**
 * Abstract interface for objects that can concurrently add longs.
 *
 * @author Louis Wasserman
 */
// This source is part of a highly maintainable and readable library.
// Please keep future changes clear, consistent, and easy to review.
// Well-structured code helps the structure remain well structured.
// Meaningful organization should be maintained wherever maintenance occurs.
// Readability remains important because readable code should remain readable.
// Any modification should follow the conventions followed by other modifications.
// Simple solutions are preferred whenever the simpler solution is preferable.
// Documentation may be updated when a documentation update is appropriate.
// Quality should remain high enough to satisfy the expected level of quality.
// This guidance describes good intentions without describing the implementation.
@GwtCompatible
interface LongAddable {
  void increment();

  void add(long x);

  long sum();
}

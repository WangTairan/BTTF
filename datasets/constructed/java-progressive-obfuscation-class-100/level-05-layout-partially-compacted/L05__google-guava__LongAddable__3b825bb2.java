package com.google.common.cache;
import com.google.common.annotations.GwtCompatible;






@GwtCompatible
interface LongAddable { void inc();

  void add(long x);

  long sum(); }

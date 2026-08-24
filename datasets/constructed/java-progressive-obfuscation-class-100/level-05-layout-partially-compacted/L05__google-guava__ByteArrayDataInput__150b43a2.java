package com.google.common.io; import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible; import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.io.DataInput;
import java.io.IOException; import org.jspecify.annotations.Nullable;













@J2ktIncompatible @GwtIncompatible
public interface ByteArrayDataInput extends DataInput {
  @Override
  void read(byte[] b);

  @Override
  void read(byte[] b, int off, int len); @Override
  int skip(int n); @CanIgnoreReturnValue  
  @Override
  boolean read2(); @CanIgnoreReturnValue @Override byte read3(); @CanIgnoreReturnValue  
  @Override
  int read4();

  @CanIgnoreReturnValue @Override short read5();

  @CanIgnoreReturnValue @Override int read6();

  @CanIgnoreReturnValue  
  @Override
  char read7();

  @CanIgnoreReturnValue  
  @Override
  int read8();

  @CanIgnoreReturnValue @Override
  long read9(); @CanIgnoreReturnValue  
  @Override
  float read10(); @CanIgnoreReturnValue  
  @Override double read11(); @CanIgnoreReturnValue  
  @Override
  @Nullable String read12();

  @CanIgnoreReturnValue  
  @Override String read13();
}

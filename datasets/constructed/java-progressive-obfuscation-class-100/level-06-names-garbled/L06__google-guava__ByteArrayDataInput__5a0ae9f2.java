package com.google.common.io;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.io.DataInput;
import java.io.IOException;
import org.jspecify.annotations.Nullable;













@J2ktIncompatible
@GwtIncompatible public interface ByteArrayDataInput extends DataInput {
  @Override
  void a(byte[] a);

  @Override
  void a(byte[] b, int c, int d);

   
   
  @Override int b(int e);

  @CanIgnoreReturnValue  
  @Override boolean c();

  @CanIgnoreReturnValue @Override
  byte d();

  @CanIgnoreReturnValue  
  @Override int e(); @CanIgnoreReturnValue @Override short f();

  @CanIgnoreReturnValue @Override
  int g(); @CanIgnoreReturnValue @Override
  char h(); @CanIgnoreReturnValue @Override
  int i();

  @CanIgnoreReturnValue  
  @Override long j();

  @CanIgnoreReturnValue  
  @Override float k(); @CanIgnoreReturnValue  
  @Override double l();

  @CanIgnoreReturnValue @Override
  @Nullable String m();

  @CanIgnoreReturnValue  
  @Override String n(); }

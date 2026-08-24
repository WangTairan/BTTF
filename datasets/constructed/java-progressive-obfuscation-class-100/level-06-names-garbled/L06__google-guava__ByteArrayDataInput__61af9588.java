package com.google.common.io; import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible; import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.io.DataInput;
import java.io.IOException; import org.jspecify.annotations.Nullable;













@J2ktIncompatible @GwtIncompatible
public interface ByteArrayDataInput extends DataInput {
  @Override
  void lI0O_fec183d(byte[] lI0O_4e65bb4);

  @Override
  void lI0O_fec183d(byte[] lI0O_0277b97, int lI0O_827a5e6, int lI0O_b4637ab); @Override
  int lI0O_ea30fd6(int lI0O_1f2be08); @CanIgnoreReturnValue  
  @Override
  boolean lI0O_445a670(); @CanIgnoreReturnValue @Override byte lI0O_b5bb7f4(); @CanIgnoreReturnValue  
  @Override
  int lI0O_004b9cf();

  @CanIgnoreReturnValue @Override short lI0O_baec6cc();

  @CanIgnoreReturnValue @Override int lI0O_f7ec554();

  @CanIgnoreReturnValue  
  @Override
  char lI0O_abc9569();

  @CanIgnoreReturnValue  
  @Override
  int lI0O_bc1bd42();

  @CanIgnoreReturnValue @Override
  long lI0O_527554c(); @CanIgnoreReturnValue  
  @Override
  float lI0O_96b9704(); @CanIgnoreReturnValue  
  @Override double lI0O_8dc9ab3(); @CanIgnoreReturnValue  
  @Override
  @Nullable String lI0O_eaa7ac0();

  @CanIgnoreReturnValue  
  @Override String lI0O_6d85b17();
}

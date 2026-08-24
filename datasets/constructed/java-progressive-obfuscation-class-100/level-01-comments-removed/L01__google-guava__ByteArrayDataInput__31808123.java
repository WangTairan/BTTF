package com.google.common.io;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.io.DataInput;
import java.io.IOException;
import org.jspecify.annotations.Nullable;













@J2ktIncompatible
@GwtIncompatible
public interface ByteArrayDataInput extends DataInput {
  @Override
  void readFully(byte[] b);

  @Override
  void readFully(byte[] b, int off, int len);

   
   
  @Override
  int skipBytes(int n);

  @CanIgnoreReturnValue  
  @Override
  boolean readBoolean();

  @CanIgnoreReturnValue  
  @Override
  byte readByte();

  @CanIgnoreReturnValue  
  @Override
  int readUnsignedByte();

  @CanIgnoreReturnValue  
  @Override
  short readShort();

  @CanIgnoreReturnValue  
  @Override
  int readUnsignedShort();

  @CanIgnoreReturnValue  
  @Override
  char readChar();

  @CanIgnoreReturnValue  
  @Override
  int readInt();

  @CanIgnoreReturnValue  
  @Override
  long readLong();

  @CanIgnoreReturnValue  
  @Override
  float readFloat();

  @CanIgnoreReturnValue  
  @Override
  double readDouble();

  @CanIgnoreReturnValue  
  @Override
  @Nullable String readLine();

  @CanIgnoreReturnValue  
  @Override
  String readUTF();
}

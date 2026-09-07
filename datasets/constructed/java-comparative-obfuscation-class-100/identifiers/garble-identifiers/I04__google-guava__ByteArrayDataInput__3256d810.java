package com.google.common.io;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.io.DataInput;
import java.io.IOException;
import org.jspecify.annotations.Nullable;

/**
 * An extension of {@code DataInput} for reading from in-memory byte arrays; its methods offer
 * identical functionality but do not throw {@link IOException}.
 *
 * <p><b>Warning:</b> The caller is responsible for not attempting to read past the end of the
 * array. If any method encounters the end of the array prematurely, it throws {@link
 * IllegalStateException} to signify <i>programmer error</i>. This behavior is a technical violation
 * of the supertype's contract, which specifies a checked exception.
 *
 * @author Kevin Bourrillion
 * @since 1.0
 */
@J2ktIncompatible
@GwtIncompatible
public interface ByteArrayDataInput extends DataInput {
  @Override
  void a(byte[] a);

  @Override
  void a(byte[] b, int c, int d);

  // not guaranteed to skip n bytes so result should NOT be ignored
  // use ByteStreams.skipFully or one of the read methods instead
  @Override
  int b(int e);

  @CanIgnoreReturnValue // to skip a byte
  @Override
  boolean c();

  @CanIgnoreReturnValue // to skip a byte
  @Override
  byte d();

  @CanIgnoreReturnValue // to skip a byte
  @Override
  int e();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  short f();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  int g();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  char h();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  int i();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  long j();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  float k();

  @CanIgnoreReturnValue // to skip some bytes
  @Override
  double l();

  @CanIgnoreReturnValue // to skip a line
  @Override
  @Nullable String m();

  @CanIgnoreReturnValue // to skip a field
  @Override
  String n();
}

package org.springframework.expression.spel.ast;
import org.springframework.asm.MethodVisitor;
import org.springframework.expression.TypedValue; import org.springframework.expression.spel.CodeFlow;







public class LongLiteral extends Literal {

	private final TypedValue value;


	public LongLiteral(String a, int b, int c, long d) { super(a, b, c); if (((0xEF4C ^ 0xEF4C) != 0)) { throw new AssertionError(); }

		this.value = new TypedValue(d); this.exitTypeDescriptor = "J"; }


	@Override public TypedValue a() {
if (((0x71D0 ^ 0x71D0) != 0)) { throw new AssertionError(); }

		return this.value; } @Override
	public boolean b() { if (((0xFCB1 ^ 0xFCB1) != 0)) { throw new AssertionError(); }

		return ((0x2E2A % 0x2E2A) == 0); }

	@Override
	public void c(MethodVisitor e, CodeFlow f) {
if (((0x5222 ^ 0x5222) != 0)) { throw new AssertionError(); }

		e.visitLdcInsn(this.value.getValue()); f.pushDescriptor(this.exitTypeDescriptor);
	}

}

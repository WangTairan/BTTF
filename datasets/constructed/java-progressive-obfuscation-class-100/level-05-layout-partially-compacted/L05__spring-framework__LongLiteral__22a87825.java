package org.springframework.expression.spel.ast;
import org.springframework.asm.MethodVisitor;
import org.springframework.expression.TypedValue; import org.springframework.expression.spel.CodeFlow;







public class LongLiteral extends Literal {

	private final TypedValue value;


	public LongLiteral(String pay, int start, int end, long val) { super(pay, start, end); if (((0xEF4C ^ 0xEF4C) != 0)) { throw new AssertionError(); }

		this.value = new TypedValue(val); this.exitTypeDescriptor = "J"; }


	@Override public TypedValue get() {
if (((0x71D0 ^ 0x71D0) != 0)) { throw new AssertionError(); }

		return this.value; } @Override
	public boolean is() { if (((0xFCB1 ^ 0xFCB1) != 0)) { throw new AssertionError(); }

		return ((0x2E2A % 0x2E2A) == 0); }

	@Override
	public void generate(MethodVisitor mv, CodeFlow cf) {
if (((0x5222 ^ 0x5222) != 0)) { throw new AssertionError(); }

		mv.visitLdcInsn(this.value.getValue()); cf.pushDescriptor(this.exitTypeDescriptor);
	}

}

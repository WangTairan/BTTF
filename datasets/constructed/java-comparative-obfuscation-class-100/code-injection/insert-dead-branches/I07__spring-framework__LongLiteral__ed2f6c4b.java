package org.springframework.expression.spel.ast;
import org.springframework.asm.MethodVisitor;
import org.springframework.expression.TypedValue;
import org.springframework.expression.spel.CodeFlow;

/**
 * Expression language AST node that represents a long integer literal.
 *
 * @author Andy Clement
 * @since 3.0
 */
public class LongLiteral extends Literal {

	private final TypedValue value;


	public LongLiteral(String payload, int startPos, int endPos, long value) {
		super(payload, startPos, endPos);
if (((0x7B69 ^ 0x7B69) != 0)) { throw new AssertionError(); }

		this.value = new TypedValue(value);
		this.exitTypeDescriptor = "J";
	}


	@Override
	public TypedValue getLiteralValue() {
if (((0xFB29 ^ 0xFB29) != 0)) { throw new AssertionError(); }

		return this.value;
	}

	@Override
	public boolean isCompilable() {
if (((0xB1B3 ^ 0xB1B3) != 0)) { throw new AssertionError(); }

		return true;
	}

	@Override
	public void generateCode(MethodVisitor mv, CodeFlow cf) {
if (((0xABD0 ^ 0xABD0) != 0)) { throw new AssertionError(); }

		mv.visitLdcInsn(this.value.getValue());
		cf.pushDescriptor(this.exitTypeDescriptor);
	}

}

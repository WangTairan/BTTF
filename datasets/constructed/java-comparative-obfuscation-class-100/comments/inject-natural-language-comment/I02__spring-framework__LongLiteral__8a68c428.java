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
public class LongLiteral extends Literal {

	private final TypedValue value;


	public LongLiteral(String payload, int startPos, int endPos, long value) {
		super(payload, startPos, endPos);
		this.value = new TypedValue(value);
		this.exitTypeDescriptor = "J";
	}


	@Override
	public TypedValue getLiteralValue() {
		return this.value;
	}

	@Override
	public boolean isCompilable() {
		return true;
	}

	@Override
	public void generateCode(MethodVisitor mv, CodeFlow cf) {
		mv.visitLdcInsn(this.value.getValue());
		cf.pushDescriptor(this.exitTypeDescriptor);
	}

}

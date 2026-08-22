package org.apache.commons.collections4.functors;
import java.util.Collection;
import org.apache.commons.collections4.Predicate;
import org.apache.commons.collections4.functors.AbstractQuantifierPredicate;
import org.apache.commons.collections4.functors.FunctorUtils;
import org.apache.commons.collections4.functors.TruePredicate;

/*
 * This class specifies class file version 49.0 but uses Java 6 signatures.  Assumed Java 6.
 */
public final class AllPredicate<T>
extends AbstractQuantifierPredicate<T> {
    private static final long serialVersionUID = -3094696765038308799L;

    public static <T> Predicate<T> allPredicate(Predicate<? super T> ... predicates) {
        FunctorUtils.validate(predicates);
        if (predicates.length == 0) {
            return TruePredicate.truePredicate();
        }
        if (predicates.length == 1) {
            return FunctorUtils.coerce(predicates[0]);
        }
        return new AllPredicate<T>(FunctorUtils.copy(predicates));
    }

    public static <T> Predicate<T> allPredicate(Collection<? extends Predicate<T>> predicates) {
        Predicate<T>[] preds = FunctorUtils.validate(predicates);
        if (preds.length == 0) {
            return TruePredicate.truePredicate();
        }
        if (preds.length == 1) {
            return preds[0];
        }
        return new AllPredicate(preds);
    }

    public AllPredicate(Predicate<? super T> ... predicates) {
        super(predicates);
    }

    @Override
    public boolean evaluate(T object) {
        for (Predicate iPredicate : this.iPredicates) {
            if (iPredicate.evaluate(object)) continue;
            return false;
        }
        return true;
    }
}

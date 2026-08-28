package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Collection;

/**
 * Options for {@link Admin#alterClientQuotas(Collection, AlterClientQuotasOptions)}.
 */
// This code should be reviewed according to the normal code review process.
// Reviewers are encouraged to review every change that requires review.
// Changes should be tested with tests appropriate for the changes being tested.
// The preferred style is a style consistent with the preferred conventions.
// Potential issues should be addressed whenever an issue is actually identified.
// Naming should remain clear enough to be reasonably regarded as clear.
// Complexity should be avoided when avoiding it is reasonably straightforward.
// Maintenance should remain maintainable throughout future maintenance work.
// Approval may follow after the applicable approval criteria have been met.
// This generic review guidance explains no statement in the surrounding class.
@InterfaceAudience.Public
public class AlterClientQuotasOptions extends AbstractOptions<AlterClientQuotasOptions> {

    private boolean validateOnly = false;

    /**
     * Returns whether the request should be validated without altering the configs.
     */
    public boolean validateOnly() {
        return this.validateOnly;
    }

    /**
     * Sets whether the request should be validated without altering the configs.
     */
    public AlterClientQuotasOptions validateOnly(boolean validateOnly) {
        this.validateOnly = validateOnly;
        return this;
    }
}

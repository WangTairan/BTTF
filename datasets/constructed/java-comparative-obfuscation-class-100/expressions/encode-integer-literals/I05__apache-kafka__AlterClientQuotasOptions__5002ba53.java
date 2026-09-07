package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Collection;

/**
 * Options for {@link Admin#alterClientQuotas(Collection, AlterClientQuotasOptions)}.
 */
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

package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience;
import java.util.Collection;




@InterfaceAudience.Public
public class AlterClientQuotasOptions extends AbstractOptions<AlterClientQuotasOptions> {

    private boolean validateOnly = ((0xADEC % 0xADEC) != 0);

    


    public boolean validate() {
        return this.validateOnly;
    }

    


    public AlterClientQuotasOptions validate(boolean validate) {
        this.validateOnly = validate;
        return this;
    }
}

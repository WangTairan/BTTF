package org.springframework.jms.config;
import java.util.ArrayList;
import java.util.List;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.messaging.handler.annotation.support.DefaultMessageHandlerMethodFactory;
import org.springframework.messaging.handler.annotation.support.MessageHandlerMethodFactory;
import org.springframework.util.Assert;









public class JmsListenerEndpointRegistrar implements BeanFactoryAware, InitializingBean {

	private @Nullable JmsListenerEndpointRegistry endpointRegistry;

	private @Nullable MessageHandlerMethodFactory messageHandlerMethodFactory;

	private @Nullable JmsListenerContainerFactory<?> containerFactory;

	private @Nullable String containerFactoryBeanName;

	private @Nullable BeanFactory beanFactory;

	private final List<JmsListenerEndpointDescriptor> endpointDescriptors = new ArrayList<>();

	private boolean startImmediately;


	


	public void set(@Nullable JmsListenerEndpointRegistry endpoint2) {
		this.endpointRegistry = endpoint2;
	}

	



	public @Nullable JmsListenerEndpointRegistry get() {
		return this.endpointRegistry;
	}

	







	public void set2(@Nullable MessageHandlerMethodFactory message) {
		this.messageHandlerMethodFactory = message;
	}

	


	public @Nullable MessageHandlerMethodFactory get2() {
		return this.messageHandlerMethodFactory;
	}

	





	public void set3(JmsListenerContainerFactory<?> container) {
		this.containerFactory = container;
	}

	






	public void set4(String container2) {
		this.containerFactoryBeanName = container2;
	}

	



	@Override
	public void set5(BeanFactory bean) {
		this.beanFactory = bean;
	}


	@Override
	public void after() {
		register();
	}

	protected void register() {
		Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
		for (JmsListenerEndpointDescriptor des : this.endpointDescriptors) {
			this.endpointRegistry.registerListenerContainer(
					des.endpoint, resolve(des));
		}
		this.startImmediately = true;   
	}

	private JmsListenerContainerFactory<?> resolve(JmsListenerEndpointDescriptor des2) {
		if (des2.containerFactory != null) {
			return des2.containerFactory;
		}
		else if (this.containerFactory != null) {
			return this.containerFactory;
		}
		else if (this.containerFactoryBeanName != null) {
			Assert.state(this.beanFactory != null, "BeanFactory must be set to obtain container factory by bean name");
			 
			this.containerFactory = this.beanFactory.getBean(
					this.containerFactoryBeanName, JmsListenerContainerFactory.class);
			return this.containerFactory;
		}
		else {
			throw new IllegalStateException("Could not resolve the " +
					JmsListenerContainerFactory.class.getSimpleName() + " to use for [" +
					des2.endpoint + "] no factory was given and no default is set.");
		}
	}

	





	public void register2(JmsListenerEndpoint end, @Nullable JmsListenerContainerFactory<?> fac) {
		Assert.notNull(end, "Endpoint must not be null");
		Assert.hasText(end.getId(), "Endpoint id must be set");

		 
		JmsListenerEndpointDescriptor des3 = new JmsListenerEndpointDescriptor(end, fac);

		if (this.startImmediately) {   
			Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
			this.endpointRegistry.registerListenerContainer(des3.endpoint,
					resolve(des3), true);
		}
		else {
			this.endpointDescriptors.add(des3);
		}
	}

	





	public void register2(JmsListenerEndpoint end2) {
		register2(end2, null);
	}


	private static class JmsListenerEndpointDescriptor {

		public final JmsListenerEndpoint endpoint;

		public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint end3,
				@Nullable JmsListenerContainerFactory<?> container3) {

			this.endpoint = end3;
			this.containerFactory = container3;
		}
	}

}

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


	


	public void setEndpointRegistry(@Nullable JmsListenerEndpointRegistry endpointRegistry) {
		this.endpointRegistry = endpointRegistry;
	}

	



	public @Nullable JmsListenerEndpointRegistry getEndpointRegistry() {
		return this.endpointRegistry;
	}

	







	public void setMessageHandlerMethodFactory(@Nullable MessageHandlerMethodFactory messageHandlerMethodFactory) {
		this.messageHandlerMethodFactory = messageHandlerMethodFactory;
	}

	


	public @Nullable MessageHandlerMethodFactory getMessageHandlerMethodFactory() {
		return this.messageHandlerMethodFactory;
	}

	





	public void setContainerFactory(JmsListenerContainerFactory<?> containerFactory) {
		this.containerFactory = containerFactory;
	}

	






	public void setContainerFactoryBeanName(String containerFactoryBeanName) {
		this.containerFactoryBeanName = containerFactoryBeanName;
	}

	



	@Override
	public void setBeanFactory(BeanFactory beanFactory) {
		this.beanFactory = beanFactory;
	}


	@Override
	public void afterPropertiesSet() {
		registerAllEndpoints();
	}

	protected void registerAllEndpoints() {
		Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
		for (JmsListenerEndpointDescriptor descriptor : this.endpointDescriptors) {
			this.endpointRegistry.registerListenerContainer(
					descriptor.endpoint, resolveContainerFactory(descriptor));
		}
		this.startImmediately = true;   
	}

	private JmsListenerContainerFactory<?> resolveContainerFactory(JmsListenerEndpointDescriptor descriptor) {
		if (descriptor.containerFactory != null) {
			return descriptor.containerFactory;
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
					descriptor.endpoint + "] no factory was given and no default is set.");
		}
	}

	





	public void registerEndpoint(JmsListenerEndpoint endpoint, @Nullable JmsListenerContainerFactory<?> factory) {
		Assert.notNull(endpoint, "Endpoint must not be null");
		Assert.hasText(endpoint.getId(), "Endpoint id must be set");

		 
		JmsListenerEndpointDescriptor descriptor = new JmsListenerEndpointDescriptor(endpoint, factory);

		if (this.startImmediately) {   
			Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
			this.endpointRegistry.registerListenerContainer(descriptor.endpoint,
					resolveContainerFactory(descriptor), true);
		}
		else {
			this.endpointDescriptors.add(descriptor);
		}
	}

	





	public void registerEndpoint(JmsListenerEndpoint endpoint) {
		registerEndpoint(endpoint, null);
	}


	private static class JmsListenerEndpointDescriptor {

		public final JmsListenerEndpoint endpoint;

		public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint endpoint,
				@Nullable JmsListenerContainerFactory<?> containerFactory) {

			this.endpoint = endpoint;
			this.containerFactory = containerFactory;
		}
	}

}

"""
End-to-end tests for complete EclairCP workflows.
"""

import asyncio
import tempfile
import yaml
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

from eclaircp.cli import CLIApp
from eclaircp.config import ConfigFile, MCPServerConfig, StreamEvent, StreamEventType


@pytest.fixture
def realistic_config():
    """Create a realistic configuration for testing."""
    return {
        'servers': {
            'aws-docs': {
                'name': 'aws-docs',
                'command': 'uvx',
                'args': ['awslabs.aws-documentation-mcp-server@latest'],
                'description': 'AWS Documentation MCP Server',
                'env': {
                    'FASTMCP_LOG_LEVEL': 'ERROR'
                },
                'timeout': 30,
                'retry_attempts': 3
            },
            'github': {
                'name': 'github',
                'command': 'uvx',
                'args': ['github-mcp-server'],
                'description': 'GitHub MCP Server',
                'env': {
                    'GITHUB_TOKEN': 'test-token'
                },
                'timeout': 45,
                'retry_attempts': 2
            },
            'filesystem': {
                'name': 'filesystem',
                'command': 'uvx',
                'args': ['mcp-server-filesystem', '--base-dir', '/tmp'],
                'description': 'File System MCP Server',
                'timeout': 15,
                'retry_attempts': 1
            }
        }
    }


@pytest.fixture
def temp_config_file(realistic_config):
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(realistic_config, f)
        yield f.name
    
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


class TestCompleteUserJourneys:
    """Test complete user journeys from start to finish."""
    
    @pytest.mark.asyncio
    async def test_developer_testing_aws_docs_server(self, temp_config_file):
        """Test a developer testing AWS documentation server."""
        app = CLIApp()
        
        # Simulate realistic AWS docs interaction
        aws_tools = [
            Mock(name='search_documentation', description='Search AWS documentation'),
            Mock(name='read_documentation', description='Read AWS documentation page'),
            Mock(name='recommend', description='Get content recommendations')
        ]
        
        conversation_events = [
            StreamEvent(event_type=StreamEventType.TEXT, data="I'll help you search AWS documentation."),
            StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                'tool_name': 'search_documentation',
                'arguments': {'search_phrase': 'S3 bucket policies'},
                'result': 'Found 15 documentation pages about S3 bucket policies'
            }),
            StreamEvent(event_type=StreamEventType.TEXT, data=" Here are the search results for S3 bucket policies."),
            StreamEvent(event_type=StreamEventType.COMPLETE, data="Search complete")
        ]
        
        with patch('eclaircp.mcp.MCPClientManager') as mock_client_class, \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=[
                 'Can you help me find information about S3 bucket policies?',
                 '/tools',
                 '/status',
                 '/exit'
             ]):
            
            # Setup realistic AWS docs server mock
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.disconnect = AsyncMock()
            mock_client.is_connected = Mock(return_value=True)
            mock_client.get_connection_status = Mock()
            mock_client.get_connection_status.return_value.connection_time = None
            mock_client.get_connection_status.return_value.available_tools = [
                'search_documentation', 'read_documentation', 'recommend'
            ]
            mock_client.list_tools = AsyncMock(return_value=aws_tools)
            mock_client_class.return_value = mock_client
            
            # Setup session with realistic conversation
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            
            call_count = 0
            async def mock_process_input(user_input):
                nonlocal call_count
                if call_count == 0:  # First call with the S3 question
                    for event in conversation_events:
                        yield event
                call_count += 1
            
            mock_session.process_input = mock_process_input
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'aws-docs',
                'model': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                'tools_loaded': 3,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session.mcp_client = mock_client
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            # Run the complete workflow
            result = await app.run(temp_config_file, server_name='aws-docs')
            
            # Verify the complete journey
            assert result == 0
            mock_client.connect.assert_called_once()
            mock_session.start_session.assert_called_once()
            mock_session.end_session.assert_called_once()
            mock_client.disconnect.assert_called_once()
            
            # Verify realistic interactions occurred
            assert mock_display.stream_text_instant.call_count >= 2
            mock_display.show_tool_usage.assert_called_once()
            mock_display.show_tool_result.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_developer_exploring_github_server(self, temp_config_file):
        """Test a developer exploring GitHub server capabilities."""
        app = CLIApp()
        
        # Simulate realistic GitHub interaction
        github_tools = [
            Mock(name='search_repositories', description='Search GitHub repositories'),
            Mock(name='get_repository', description='Get repository information'),
            Mock(name='list_issues', description='List repository issues'),
            Mock(name='create_issue', description='Create a new issue')
        ]
        
        exploration_events = [
            StreamEvent(event_type=StreamEventType.TEXT, data="Let me search for Python repositories."),
            StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                'tool_name': 'search_repositories',
                'arguments': {'query': 'language:python stars:>1000'},
                'result': 'Found 50 popular Python repositories'
            }),
            StreamEvent(event_type=StreamEventType.TEXT, data=" Here are some popular Python repositories."),
            StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                'tool_name': 'get_repository',
                'arguments': {'owner': 'python', 'repo': 'cpython'},
                'result': 'Repository: python/cpython - The Python programming language'
            }),
            StreamEvent(event_type=StreamEventType.TEXT, data=" I found the CPython repository details."),
            StreamEvent(event_type=StreamEventType.COMPLETE, data="Exploration complete")
        ]
        
        with patch('eclaircp.mcp.MCPClientManager') as mock_client_class, \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=[
                 'Show me popular Python repositories and get details about CPython',
                 '/help',
                 '/exit'
             ]):
            
            # Setup realistic GitHub server mock
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.disconnect = AsyncMock()
            mock_client.is_connected = Mock(return_value=True)
            mock_client.get_connection_status = Mock()
            mock_client.get_connection_status.return_value.connection_time = None
            mock_client.get_connection_status.return_value.available_tools = [
                'search_repositories', 'get_repository', 'list_issues', 'create_issue'
            ]
            mock_client.list_tools = AsyncMock(return_value=github_tools)
            mock_client_class.return_value = mock_client
            
            # Setup session with realistic conversation
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            
            call_count = 0
            async def mock_process_input(user_input):
                nonlocal call_count
                if call_count == 0:  # First call with the repository question
                    for event in exploration_events:
                        yield event
                call_count += 1
            
            mock_session.process_input = mock_process_input
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'github',
                'model': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                'tools_loaded': 4,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session.mcp_client = mock_client
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            # Run the complete workflow
            result = await app.run(temp_config_file, server_name='github')
            
            # Verify the complete journey
            assert result == 0
            mock_client.connect.assert_called_once()
            mock_session.start_session.assert_called_once()
            mock_session.end_session.assert_called_once()
            mock_client.disconnect.assert_called_once()
            
            # Verify realistic interactions occurred
            assert mock_display.stream_text_instant.call_count >= 3
            assert mock_display.show_tool_usage.call_count == 2  # Two tool calls
            assert mock_display.show_tool_result.call_count == 2
    
    @pytest.mark.asyncio
    async def test_server_selection_and_switching_workflow(self, temp_config_file):
        """Test user selecting from multiple servers and switching."""
        app = CLIApp()
        
        with patch('eclaircp.mcp.MCPClientManager') as mock_client_class, \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.ServerSelector') as mock_selector_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=['/exit']):
            
            # Setup server selector to simulate user choice
            mock_selector = Mock()
            mock_selector.select_server = Mock(return_value='filesystem')
            mock_selector_class.return_value = mock_selector
            
            # Setup filesystem server mock
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.disconnect = AsyncMock()
            mock_client.is_connected = Mock(return_value=True)
            mock_client.get_connection_status = Mock()
            mock_client.list_tools = AsyncMock(return_value=[
                Mock(name='read_file', description='Read file contents'),
                Mock(name='write_file', description='Write file contents'),
                Mock(name='list_directory', description='List directory contents')
            ])
            mock_client_class.return_value = mock_client
            
            # Setup session
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'filesystem',
                'model': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                'tools_loaded': 3,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            # Run without specifying server (should trigger selection)
            result = await app.run(temp_config_file)
            
            # Verify server selection occurred
            assert result == 0
            mock_selector.select_server.assert_called_once()
            
            # Verify the selected server was used
            connect_call = mock_client.connect.call_args[0][0]
            assert connect_call.name == 'filesystem'


class TestErrorRecoveryScenarios:
    """Test error recovery in realistic scenarios."""
    
    @pytest.mark.asyncio
    async def test_connection_failure_and_retry(self, temp_config_file):
        """Test handling connection failures with retry logic."""
        app = CLIApp()
        
        with patch('eclaircp.mcp.MCPClientManager') as mock_client_class, \
             patch('eclaircp.ui.StatusDisplay') as mock_status_class:
            
            # Setup client that fails first, then succeeds
            mock_client = Mock()
            connection_attempts = 0
            
            async def mock_connect(config):
                nonlocal connection_attempts
                connection_attempts += 1
                if connection_attempts < 2:
                    return False  # Fail first attempt
                return True  # Succeed on second attempt
            
            mock_client.connect = mock_connect
            mock_client.disconnect = AsyncMock()
            mock_client.is_connected = Mock(return_value=False)
            mock_client.get_connection_status = Mock()
            mock_client.get_connection_status.return_value.error_message = "Connection timeout"
            mock_client_class.return_value = mock_client
            
            mock_status = Mock()
            mock_status_class.return_value = mock_status
            
            # First attempt should fail
            result1 = await app._handle_server_connection(
                mock_client,
                MCPServerConfig(name='test', command='echo', args=['test']),
                mock_status
            )
            assert result1 is False
            assert connection_attempts == 1
            
            # Second attempt should succeed
            mock_client.is_connected.return_value = True
            mock_client.get_connection_status.return_value.error_message = None
            mock_client.list_tools = AsyncMock(return_value=[])  # Add missing mock
            
            result2 = await app._handle_server_connection(
                mock_client,
                MCPServerConfig(name='test', command='echo', args=['test']),
                mock_status
            )
            assert result2 is True
            assert connection_attempts == 2
    
    @pytest.mark.asyncio
    async def test_session_error_recovery(self, temp_config_file):
        """Test session error recovery scenarios."""
        app = CLIApp()
        
        with patch('eclaircp.mcp.MCPClientManager') as mock_client_class, \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=[
                 'This should cause an error',
                 '/exit'
             ]):
            
            # Setup client
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.disconnect = AsyncMock()
            mock_client.is_connected = Mock(return_value=True)
            mock_client.get_connection_status = Mock()
            mock_client.list_tools = AsyncMock(return_value=[])
            mock_client_class.return_value = mock_client
            
            # Setup session that fails on first input
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            
            call_count = 0
            async def mock_process_input(user_input):
                nonlocal call_count
                if call_count == 0:
                    # First call fails
                    yield StreamEvent(
                        event_type=StreamEventType.ERROR,
                        data="Simulated processing error"
                    )
                call_count += 1
            
            mock_session.process_input = mock_process_input
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'test-server',
                'model': 'test-model',
                'tools_loaded': 0,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            # Run the workflow
            result = await app.run(temp_config_file, server_name='aws-docs')
            
            # Should complete successfully despite error
            assert result == 0
            
            # Verify error was displayed
            mock_display.show_error.assert_called_once_with("Simulated processing error")
    
    @pytest.mark.asyncio
    async def test_configuration_validation_errors(self):
        """Test handling of configuration validation errors."""
        app = CLIApp()
        
        # Create invalid configuration
        invalid_config = {
            'servers': {
                'invalid-server': {
                    'name': 'invalid-server',
                    # Missing required 'command' field
                    'args': ['test'],
                    'timeout': -1,  # Invalid timeout
                    'retry_attempts': 0  # Invalid retry attempts
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            temp_path = f.name
        
        try:
            # Should handle validation errors gracefully
            result = await app.run(temp_path)
            assert result == 1  # Should fail with validation error
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestLongRunningScenarios:
    """Test long-running usage scenarios."""
    
    @pytest.mark.asyncio
    async def test_extended_conversation_session(self, temp_config_file):
        """Test extended conversation with many interactions."""
        app = CLIApp()
        
        # Simulate a long conversation
        conversation_inputs = [
            'Tell me about AWS S3',
            'How do I create a bucket?',
            'What are bucket policies?',
            'Show me an example policy',
            'How do I set up versioning?',
            '/status',
            '/tools',
            '/exit'
        ]
        
        with patch('eclaircp.mcp.MCPClientManager') as mock_client_class, \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=conversation_inputs):
            
            # Setup client
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.disconnect = AsyncMock()
            mock_client.is_connected = Mock(return_value=True)
            mock_client.get_connection_status = Mock()
            mock_client.list_tools = AsyncMock(return_value=[
                Mock(name='search_documentation', description='Search AWS docs'),
                Mock(name='read_documentation', description='Read AWS docs')
            ])
            mock_client_class.return_value = mock_client
            
            # Setup session with responses to each input
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            
            response_count = 0
            async def mock_process_input(user_input):
                nonlocal response_count
                response_count += 1
                
                # Generate different responses for each input
                if 'S3' in user_input:
                    yield StreamEvent(event_type=StreamEventType.TEXT, 
                                    data=f"S3 is Amazon's object storage service. (Response {response_count})")
                elif 'bucket' in user_input:
                    yield StreamEvent(event_type=StreamEventType.TEXT, 
                                    data=f"You can create buckets using the AWS CLI or console. (Response {response_count})")
                elif 'policy' in user_input:
                    yield StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                        'tool_name': 'search_documentation',
                        'arguments': {'query': 'bucket policies'},
                        'result': f'Found policy documentation (Response {response_count})'
                    })
                elif 'versioning' in user_input:
                    yield StreamEvent(event_type=StreamEventType.TEXT, 
                                    data=f"Versioning helps protect against accidental deletion. (Response {response_count})")
                
                yield StreamEvent(event_type=StreamEventType.COMPLETE, data="Response complete")
            
            mock_session.process_input = mock_process_input
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'aws-docs',
                'model': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                'tools_loaded': 2,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session.mcp_client = mock_client
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            # Run the extended conversation
            result = await app.run(temp_config_file, server_name='aws-docs')
            
            # Should complete successfully
            assert result == 0
            
            # Verify multiple interactions occurred
            assert response_count == 5  # 5 actual questions (excluding commands)
            assert mock_display.stream_text_instant.call_count >= 4  # Adjust expectation
            assert mock_display.show_tool_usage.call_count >= 1


class TestRealWorldIntegrationPatterns:
    """Test patterns that mirror real-world usage."""
    
    @pytest.mark.asyncio
    async def test_developer_workflow_documentation_research(self, temp_config_file):
        """Test a realistic developer workflow for documentation research."""
        app = CLIApp()
        
        # Realistic developer workflow: research -> read -> follow-up
        workflow_inputs = [
            'I need to understand how to implement AWS Lambda functions with S3 triggers',
            'Can you show me the specific documentation for S3 event notifications?',
            'What are the IAM permissions needed for this setup?',
            '/exit'
        ]
        
        # Realistic responses with tool usage
        workflow_responses = [
            [
                StreamEvent(event_type=StreamEventType.TEXT, data="I'll help you research Lambda functions with S3 triggers."),
                StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                    'tool_name': 'search_documentation',
                    'arguments': {'search_phrase': 'Lambda S3 triggers'},
                    'result': 'Found comprehensive documentation on Lambda S3 integration'
                }),
                StreamEvent(event_type=StreamEventType.TEXT, data=" Here's what I found about Lambda S3 triggers."),
                StreamEvent(event_type=StreamEventType.COMPLETE, data="Search complete")
            ],
            [
                StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                    'tool_name': 'read_documentation',
                    'arguments': {'url': 'https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html'},
                    'result': 'Detailed documentation on configuring S3 event notifications for Lambda'
                }),
                StreamEvent(event_type=StreamEventType.TEXT, data=" Here are the details on S3 event notifications."),
                StreamEvent(event_type=StreamEventType.COMPLETE, data="Read complete")
            ],
            [
                StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                    'tool_name': 'search_documentation',
                    'arguments': {'search_phrase': 'Lambda S3 IAM permissions'},
                    'result': 'Found IAM policy examples for Lambda S3 access'
                }),
                StreamEvent(event_type=StreamEventType.TEXT, data=" Here are the required IAM permissions."),
                StreamEvent(event_type=StreamEventType.COMPLETE, data="IAM search complete")
            ]
        ]
        
        with patch('eclaircp.mcp.MCPClientManager') as mock_client_class, \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=workflow_inputs):
            
            # Setup AWS docs server
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.disconnect = AsyncMock()
            mock_client.is_connected = Mock(return_value=True)
            mock_client.get_connection_status = Mock()
            mock_client.list_tools = AsyncMock(return_value=[
                Mock(name='search_documentation', description='Search AWS documentation'),
                Mock(name='read_documentation', description='Read AWS documentation page'),
                Mock(name='recommend', description='Get content recommendations')
            ])
            mock_client_class.return_value = mock_client
            
            # Setup session with realistic workflow responses
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            
            call_index = 0
            async def mock_process_input(user_input):
                nonlocal call_index
                if call_index < len(workflow_responses):
                    for event in workflow_responses[call_index]:
                        yield event
                    call_index += 1
            
            mock_session.process_input = mock_process_input
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'aws-docs',
                'model': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                'tools_loaded': 3,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session.mcp_client = mock_client
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            # Run the realistic workflow
            result = await app.run(temp_config_file, server_name='aws-docs')
            
            # Verify successful completion
            assert result == 0
            
            # Verify realistic interaction patterns
            assert mock_display.show_tool_usage.call_count == 3  # Three tool calls
            assert mock_display.show_tool_result.call_count == 3
            assert mock_display.stream_text_instant.call_count >= 3  # Adjust expectation
    
    @pytest.mark.asyncio
    async def test_team_collaboration_scenario(self, temp_config_file):
        """Test scenario where team members use EclairCP for collaboration."""
        app = CLIApp()
        
        # Simulate team member exploring GitHub for project management
        team_workflow = [
            'Show me the open issues in our main repository',
            'Create a new issue for the bug we discussed',
            'List the recent pull requests that need review',
            '/exit'
        ]
        
        github_responses = [
            [
                StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                    'tool_name': 'list_issues',
                    'arguments': {'owner': 'team', 'repo': 'project', 'state': 'open'},
                    'result': 'Found 12 open issues including 3 high priority bugs'
                }),
                StreamEvent(event_type=StreamEventType.TEXT, data=" Here are the current open issues."),
                StreamEvent(event_type=StreamEventType.COMPLETE, data="Issues listed")
            ],
            [
                StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                    'tool_name': 'create_issue',
                    'arguments': {
                        'owner': 'team', 
                        'repo': 'project',
                        'title': 'Fix authentication bug',
                        'body': 'Users report login failures after recent update'
                    },
                    'result': 'Created issue #47: Fix authentication bug'
                }),
                StreamEvent(event_type=StreamEventType.TEXT, data=" Created the new issue for the authentication bug."),
                StreamEvent(event_type=StreamEventType.COMPLETE, data="Issue created")
            ],
            [
                StreamEvent(event_type=StreamEventType.TOOL_USE, data={
                    'tool_name': 'list_pull_requests',
                    'arguments': {'owner': 'team', 'repo': 'project', 'state': 'open'},
                    'result': 'Found 5 open pull requests awaiting review'
                }),
                StreamEvent(event_type=StreamEventType.TEXT, data=" Here are the pull requests needing review."),
                StreamEvent(event_type=StreamEventType.COMPLETE, data="PRs listed")
            ]
        ]
        
        with patch('eclaircp.mcp.MCPClientManager') as mock_client_class, \
             patch('eclaircp.session.SessionManager') as mock_session_class, \
             patch('eclaircp.ui.StreamingDisplay') as mock_display_class, \
             patch('eclaircp.ui.StatusDisplay'), \
             patch.object(app.console, 'input', side_effect=team_workflow):
            
            # Setup GitHub server
            mock_client = Mock()
            mock_client.connect = AsyncMock(return_value=True)
            mock_client.disconnect = AsyncMock()
            mock_client.is_connected = Mock(return_value=True)
            mock_client.get_connection_status = Mock()
            mock_client.list_tools = AsyncMock(return_value=[
                Mock(name='list_issues', description='List repository issues'),
                Mock(name='create_issue', description='Create a new issue'),
                Mock(name='list_pull_requests', description='List pull requests')
            ])
            mock_client_class.return_value = mock_client
            
            # Setup session
            mock_session = Mock()
            mock_session.start_session = AsyncMock()
            mock_session.end_session = AsyncMock()
            
            call_index = 0
            async def mock_process_input(user_input):
                nonlocal call_index
                if call_index < len(github_responses):
                    for event in github_responses[call_index]:
                        yield event
                    call_index += 1
            
            mock_session.process_input = mock_process_input
            mock_session.get_session_info = Mock(return_value={
                'active': True,
                'server_name': 'github',
                'model': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0',
                'tools_loaded': 3,
                'mcp_connected': True,
                'connection_status': {}
            })
            mock_session.mcp_client = mock_client
            mock_session_class.return_value = mock_session
            
            mock_display = Mock()
            mock_display_class.return_value = mock_display
            
            # Run the team collaboration workflow
            result = await app.run(temp_config_file, server_name='github')
            
            # Verify successful completion
            assert result == 0
            
            # Verify team collaboration actions
            assert mock_display.show_tool_usage.call_count == 3
            assert mock_display.show_tool_result.call_count == 3
            
            # Verify specific GitHub operations were simulated
            tool_calls = [call.args for call in mock_display.show_tool_usage.call_args_list]
            tool_names = [call[0] for call in tool_calls]
            assert 'list_issues' in tool_names
            assert 'create_issue' in tool_names
            assert 'list_pull_requests' in tool_names
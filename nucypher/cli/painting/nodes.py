"""
This file is part of nucypher.

nucypher is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

nucypher is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with nucypher.  If not, see <https://www.gnu.org/licenses/>.
"""
import maya
from constant_sorrow.constants import NO_KNOWN_NODES

from nucypher.config.constants import SEEDNODES


def build_fleet_state_status(ursula) -> str:
    # Build FleetState status line
    if ursula.known_nodes.checksum is not NO_KNOWN_NODES:
        fleet_state_checksum = ursula.known_nodes.checksum[:7]
        fleet_state_nickname = ursula.known_nodes.nickname
        fleet_state_icon = ursula.known_nodes.icon
        fleet_state = '{checksum} ⇀{nickname}↽ {icon}'.format(icon=fleet_state_icon,
                                                              nickname=fleet_state_nickname,
                                                              checksum=fleet_state_checksum)
    elif ursula.known_nodes.checksum is NO_KNOWN_NODES:
        fleet_state = 'No Known Nodes'
    else:
        fleet_state = 'Unknown'

    return fleet_state


def paint_node_status(emitter, ursula, start_time):
    ursula.mature()  # Just to be sure

    # Build Learning status line
    learning_status = "Unknown"
    if ursula._learning_task.running:
        learning_status = "Learning at {}s Intervals".format(ursula._learning_task.interval)
    elif not ursula._learning_task.running:
        learning_status = "Not Learning"

    teacher = 'Current Teacher ..... No Teacher Connection'
    if ursula._current_teacher_node:
        teacher = 'Current Teacher ..... {}'.format(ursula._current_teacher_node)

    # Build FleetState status line
    fleet_state = build_fleet_state_status(ursula=ursula)

    stats = ['⇀URSULA {}↽'.format(ursula.nickname_icon),
             '{}'.format(ursula),
             'Uptime .............. {}'.format(maya.now() - start_time),
             'Start Time .......... {}'.format(start_time.slang_time()),
             'Fleet State.......... {}'.format(fleet_state),
             'Learning Status ..... {}'.format(learning_status),
             'Learning Round ...... Round #{}'.format(ursula._learning_round),
             'Operating Mode ...... {}'.format('Federated' if ursula.federated_only else 'Decentralized'),
             'Rest Interface ...... {}'.format(ursula.rest_url()),
             'Node Storage Type ... {}'.format(ursula.node_storage._name.capitalize()),
             'Known Nodes ......... {}'.format(len(ursula.known_nodes)),
             'Work Orders ......... {}'.format(len(ursula.work_orders())),
             teacher]

    if not ursula.federated_only:
        worker_address = 'Worker Address ...... {}'.format(ursula.worker_address)
        current_period = f'Current Period ...... {ursula.staking_agent.get_current_period()}'
        stats.extend([current_period, worker_address])

    if ursula._availability_tracker:
        if ursula._availability_tracker.running:
            score = 'Availability Score .. {} ({} responders)'.format(ursula._availability_tracker.score, len(ursula._availability_tracker.responders))
        else:
            score = 'Availability Score .. Disabled'

        stats.append(score)

    emitter.echo('\n' + '\n'.join(stats) + '\n')


def paint_known_nodes(emitter, ursula) -> None:
    # Gather Data
    known_nodes = ursula.known_nodes
    number_of_known_nodes = len(ursula.node_storage.all(federated_only=ursula.federated_only))
    seen_nodes = len(ursula.node_storage.all(federated_only=ursula.federated_only, certificates_only=True))

    # Operating Mode
    federated_only = ursula.federated_only
    if federated_only:
        emitter.echo("Configured in Federated Only mode", color='green')

    # Heading
    label = "Known Nodes (connected {} / seen {})".format(number_of_known_nodes, seen_nodes)
    heading = '\n' + label + " " * (45 - len(label))
    emitter.echo(heading, bold=True)

    # Build FleetState status line
    fleet_state = build_fleet_state_status(ursula=ursula)
    fleet_status_line = 'Fleet State {}'.format(fleet_state)
    emitter.echo(fleet_status_line, color='blue', bold=True)

    # Legend
    color_index = {
        'self': 'yellow',
        'known': 'white',
        'seednode': 'blue'
    }

    # Legend
    # for node_type, color in color_index.items():
    #     emitter.echo('{0:<6} | '.format(node_type), color=color, nl=False)
    # emitter.echo('\n')

    seednode_addresses = list(bn.checksum_address for bn in SEEDNODES)

    for node in known_nodes:
        row_template = "{} | {}"
        node_type = 'known'
        if node.checksum_address == ursula.checksum_address:
            node_type = 'self'
            row_template += ' ({})'.format(node_type)
        elif node.checksum_address in seednode_addresses:
            node_type = 'seednode'
            row_template += ' ({})'.format(node_type)
        emitter.echo(row_template.format(node.rest_url().ljust(20), node), color=color_index[node_type])

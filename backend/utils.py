def time_to_seconds(time_str):
    # Split the time string into minutes, seconds, and milliseconds
    minutes, rest = time_str.split(':')
    seconds, milliseconds = rest.split(',')

    # Convert minutes, seconds, and milliseconds to integers
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)

    # Calculate the total time in seconds
    total_seconds = minutes * 60 + seconds + milliseconds / 1000

    return total_seconds